#!/usr/bin/env python3
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone

API = "https://api.sleeper.app/v1"
META_API = "https://api.meta.ai/v1"
REPO = os.environ.get("GITHUB_REPOSITORY", "wlatic/draft-center")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MUSE_KEY = os.environ.get("MUSE_API_KEY", "")
ANALYSIS_BRANCH = os.environ.get("ANALYSIS_BRANCH", "analysis")
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "12"))
MAX_SECONDS = int(os.environ.get("MAX_SECONDS", str(5 * 60 * 60)))


def http_json(url, *, method="GET", headers=None, body=None, timeout=20):
    hdr = {"Accept": "application/json", "User-Agent": "DraftCenter-AI"}
    if headers:
        hdr.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdr.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdr, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8")
        return json.loads(raw) if raw else None


def sleeper(path):
    return http_json(API + path)


def read_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def scoring_field(draft):
    s = draft.get("settings") or {}
    if int(s.get("slots_super_flex") or 0) > 0 or int(s.get("slots_qb") or 0) > 1:
        return "adp_2qb"
    scoring = str((draft.get("metadata") or {}).get("scoring_type") or "").lower()
    if "half" in scoring:
        return "adp_half_ppr"
    if "ppr" in scoring:
        return "adp_ppr"
    return "adp_std"


def load_adp(draft):
    season = str(draft.get("season") or datetime.now(timezone.utc).year)
    field = scoring_field(draft)
    try:
        rows = sleeper(f"/projections/nfl/{season}?season_type=regular&order_by={field}")
    except Exception as e:
        print(f"ADP unavailable: {e}", flush=True)
        return {}, [], field
    by_id, ordered = {}, []
    for x in rows if isinstance(rows, list) else []:
        stats = x.get("stats") or {}
        try:
            adp = float(stats.get(field))
        except (TypeError, ValueError):
            continue
        if not (0 < adp < 999):
            continue
        p = x.get("player") or {}
        pid = str(x.get("player_id") or p.get("player_id") or "")
        if not pid:
            continue
        name = p.get("full_name") or " ".join(v for v in [p.get("first_name"), p.get("last_name")] if v) or pid
        pos = p.get("position") or ((p.get("fantasy_positions") or [""])[0] if isinstance(p.get("fantasy_positions"), list) else "")
        row = {"player_id": pid, "adp": adp, "name": name, "position": pos or "?", "team": p.get("team") or x.get("team") or "FA"}
        by_id[pid] = row
        ordered.append(row)
    ordered.sort(key=lambda r: r["adp"])
    return by_id, ordered, field


def pick_name(p):
    m = p.get("metadata") or {}
    return " ".join(v for v in [m.get("first_name"), m.get("last_name")] if v).strip() or m.get("full_name") or str(p.get("player_id") or "Unknown")


def pick_pos(p):
    return str((p.get("metadata") or {}).get("position") or "?").upper()


def owner_maps(draft):
    order = draft.get("draft_order") or {}
    slot_to_uid = {int(slot): str(uid) for uid, slot in order.items() if str(slot).isdigit()}
    return slot_to_uid


def display_owner(uid, profiles, aliases):
    p = profiles.get(uid) or {}
    username = str(p.get("username") or "").lower()
    return aliases.get(username) or p.get("display_name") or p.get("username") or (f"Team {uid[-4:]}" if uid else "Unknown")


def load_profiles(draft, cache):
    aliases = {str(k).lower(): str(v) for k, v in (read_config().get("broadcastNames") or {}).items()}
    for uid in (draft.get("draft_order") or {}).keys():
        uid = str(uid)
        if uid in cache:
            continue
        try:
            cache[uid] = sleeper(f"/user/{urllib.parse.quote(uid)}") or {}
        except Exception:
            cache[uid] = {}
    return aliases


def add_fact(out, fact_id, title, detail, score, tone=""):
    out.append({"id": fact_id, "title": title, "detail": detail, "score": float(score), "tone": tone})


def build_candidates(draft, picks, adp_by_id, adp_rows, profiles, aliases):
    facts = []
    teams = max(1, int((draft.get("settings") or {}).get("teams") or 10))
    live = [p for p in picks if not bool((p.get("metadata") or {}).get("is_keeper"))]
    next_ordinal = len(live) + 1
    round_no = ((next_ordinal - 1) // teams) + 1
    round_start = (round_no - 1) * teams + 1
    round_picks = [p for p in live if round_start <= int(p.get("pick_no") or 0) <= round_start + teams - 1]

    # Current round position shape.
    counts = Counter(pick_pos(p) for p in round_picks)
    for pos, n in counts.most_common(3):
        if n:
            add_fact(facts, f"round:{round_no}:{pos}", f"{n} {pos}{'' if n == 1 else 's'} in Round {round_no}", f"{len(round_picks)} of {teams} picks are complete in the round.", 24 + n * 3, "hot" if n >= 4 else "")

    # Position runs in recent picks.
    recent = live[-6:]
    rc = Counter(pick_pos(p) for p in recent)
    for pos, n in rc.items():
        if n >= 4:
            add_fact(facts, f"run:{len(live)}:{pos}", f"{pos} RUN: {n} of the last {len(recent)}", "The room has been hammering the same position lately.", 72 + n, "hot")

    # Market movers. Actual ordinal is pick_no for live non-keeper drafts here; keepers are filtered from display but ADP comparison uses live ordinal.
    for ordinal, p in enumerate(live, start=1):
        row = adp_by_id.get(str(p.get("player_id") or ""))
        if not row:
            continue
        delta = ordinal - row["adp"]
        name = pick_name(p)
        if delta >= 8:
            add_fact(facts, f"value:{p.get('player_id')}:{ordinal}", f"VALUE: {name}", f"Selected {round(delta)} picks after Sleeper ADP {row['adp']:.1f}.", 70 + min(30, delta), "good")
        elif delta <= -8:
            add_fact(facts, f"reach:{p.get('player_id')}:{ordinal}", f"EARLY: {name}", f"Selected {abs(round(delta))} picks ahead of Sleeper ADP {row['adp']:.1f}.", 68 + min(30, abs(delta)), "alert")

    # Best available / slider.
    picked_ids = {str(p.get("player_id") or "") for p in live}
    for row in adp_rows:
        if row["player_id"] in picked_ids:
            continue
        slide = next_ordinal - row["adp"]
        if slide >= 5:
            add_fact(facts, f"available:{row['player_id']}:{next_ordinal}", f"STILL THERE: {row['name']}", f"Now {round(slide)} picks past Sleeper ADP {row['adp']:.1f} and still available.", 58 + min(25, slide), "good")
        break

    # Team roster shapes.
    slot_to_uid = owner_maps(draft)
    team_counts = defaultdict(Counter)
    for p in live:
        slot = int(p.get("draft_slot") or 0)
        uid = slot_to_uid.get(slot, "")
        if uid:
            team_counts[uid][pick_pos(p)] += 1
    for uid, c in team_counts.items():
        total = sum(c.values())
        owner = display_owner(uid, profiles, aliases)
        if total >= 4:
            if c["RB"] == 0 and c["WR"] >= 3:
                add_fact(facts, f"build:{uid}:zerorb:{total}", f"ZERO-RB WATCH: {owner}", f"Through {total} selections: {c['WR']} WR, {c['RB']} RB.", 64 + c["WR"], "hot")
            elif c["WR"] >= 4 and c["RB"] >= 1:
                add_fact(facts, f"build:{uid}:wrheavy:{total}", f"WR-HEAVY: {owner}", f"Through {total} selections: {c['WR']} WR and {c['RB']} RB.", 52 + c["WR"], "")
            elif c["RB"] >= 4:
                add_fact(facts, f"build:{uid}:rbheavy:{total}", f"RB-HEAVY: {owner}", f"Through {total} selections: {c['RB']} RB and {c['WR']} WR.", 52 + c["RB"], "")

    # First QB / TE timing.
    for pos in ("QB", "TE"):
        first = next((p for p in live if pick_pos(p) == pos), None)
        if first:
            o = live.index(first) + 1
            add_fact(facts, f"first:{pos}:{o}", f"FIRST {pos}: {pick_name(first)}", f"The first {pos} came off the board at overall pick {o}.", 42, "")
        elif len(live) >= teams:
            add_fact(facts, f"none:{pos}:{round_no}", f"NO {pos} YET", f"No {pos} has been selected through {len(live)} live picks.", 44, "good")

    # De-duplicate and sort.
    best = {}
    for f in facts:
        if f["id"] not in best or f["score"] > best[f["id"]]["score"]:
            best[f["id"]] = f
    return sorted(best.values(), key=lambda x: (-x["score"], x["id"]))[:24], round_no, next_ordinal


def discover_model():
    if not MUSE_KEY:
        return None
    try:
        data = http_json(META_API + "/models", headers={"Authorization": f"Bearer {MUSE_KEY}"})
        ids = [str(x.get("id")) for x in (data or {}).get("data", []) if x.get("id")]
    except Exception as e:
        print(f"Muse model discovery failed: {e}", flush=True)
        return "muse-spark-1.3-contributor"
    prefs = ["muse-spark-1.3-contributor", "muse-spark-1.2-contributor"]
    for p in prefs:
        if p in ids:
            return p
    contributors = [x for x in ids if "muse-spark" in x and "contributor" in x]
    if contributors:
        return sorted(contributors, reverse=True)[0]
    muse = [x for x in ids if "muse-spark" in x]
    return sorted(muse, reverse=True)[0] if muse else "muse-spark-1.3-contributor"


def muse_select(model, candidates, history, round_no, next_ordinal):
    if not MUSE_KEY or not model or not candidates:
        return None
    compact = [{k: f[k] for k in ("id", "title", "detail", "score")} for f in candidates]
    prompt = {
        "role": "Fantasy-football DraftCenter studio editor",
        "rules": [
            "Choose the four most interesting facts for a live TV panel.",
            "You may ONLY select supplied fact IDs. Never invent stats, players, teams, causes, or draft strategy.",
            "For each selected fact, optionally add a short punchy take of at most 12 words.",
            "Takes must contain no digits and no new factual claim; personality only.",
            "Avoid recently used fact IDs when good alternatives exist.",
            "Return JSON only with keys headline and selections. selections is [{id,take}].",
        ],
        "state": {"round": round_no, "nextOverallPick": next_ordinal},
        "recentFactIds": history[-16:],
        "facts": compact,
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise live fantasy-football draft studio editor. Output strict JSON only."},
            {"role": "user", "content": json.dumps(prompt, separators=(",", ":"))},
        ],
        "temperature": 0.65,
        "max_tokens": 500,
        "response_format": {"type": "json_object"},
    }
    data = http_json(META_API + "/chat/completions", method="POST", headers={"Authorization": f"Bearer {MUSE_KEY}"}, body=body, timeout=45)
    text = (((data or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
    return json.loads(text)


def assemble_analysis(draft_id, candidates, model_result, model, round_no, next_ordinal, history):
    by_id = {f["id"]: f for f in candidates}
    selected, takes = [], {}
    headline = "DRAFTCENTER DESK"
    if isinstance(model_result, dict):
        h = str(model_result.get("headline") or "").strip()
        if h:
            headline = h[:70]
        for item in model_result.get("selections") or []:
            fid = str(item.get("id") or "")
            take = str(item.get("take") or "").strip()
            if fid in by_id and fid not in selected:
                selected.append(fid)
                if take and not re.search(r"\d", take):
                    takes[fid] = take[:100]
    for f in candidates:
        if len(selected) >= 4:
            break
        if f["id"] not in selected:
            selected.append(f["id"])
    items = []
    for fid in selected[:4]:
        f = dict(by_id[fid])
        take = takes.get(fid, "")
        if take:
            f["detail"] = f"{f['detail']} — {take}"
        f.pop("score", None)
        items.append(f)
        history.append(fid)
    del history[:-40]
    return {
        "draftId": str(draft_id),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "revision": f"{draft_id}:{next_ordinal}:{int(time.time())}",
        "round": round_no,
        "nextOverallPick": next_ordinal,
        "headline": headline,
        "model": model or "deterministic",
        "items": items,
    }


def publish_analysis(payload):
    if not TOKEN:
        print("No GITHUB_TOKEN; cannot publish analysis", flush=True)
        return
    path = "analysis.json"
    api = f"https://api.github.com/repos/{REPO}/contents/{path}"
    sha = None
    try:
        current = http_json(api + "?ref=" + urllib.parse.quote(ANALYSIS_BRANCH), headers={"Authorization": f"Bearer {TOKEN}"})
        sha = (current or {}).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    body = {
        "message": f"Update DraftCenter AI analysis for pick {payload.get('nextOverallPick')}",
        "content": base64.b64encode((json.dumps(payload, indent=2) + "\n").encode("utf-8")).decode("ascii"),
        "branch": ANALYSIS_BRANCH,
    }
    if sha:
        body["sha"] = sha
    http_json(api, method="PUT", headers={"Authorization": f"Bearer {TOKEN}", "X-GitHub-Api-Version": "2022-11-28"}, body=body, timeout=30)
    print(f"Published AI analysis: round {payload['round']} next {payload['nextOverallPick']} via {payload['model']}", flush=True)


def main():
    cfg = read_config()
    draft_id = str(cfg.get("draftId") or "").strip()
    if not draft_id:
        raise SystemExit("config.json has no draftId")
    model = discover_model()
    print(f"DraftCenter AI watcher: draft {draft_id}; model {model or 'deterministic only'}", flush=True)
    profiles = {}
    aliases = {}
    history = []
    adp_by_id, adp_rows, adp_field = {}, [], ""
    last_signature = None
    started = time.time()

    while time.time() - started < MAX_SECONDS:
        try:
            draft = sleeper(f"/draft/{urllib.parse.quote(draft_id)}")
            picks = sleeper(f"/draft/{urllib.parse.quote(draft_id)}/picks")
            if not isinstance(picks, list):
                picks = []
            picks.sort(key=lambda p: int(p.get("pick_no") or 0))
            if not adp_rows:
                adp_by_id, adp_rows, adp_field = load_adp(draft)
                print(f"ADP field: {adp_field}; {len(adp_rows)} ranked players", flush=True)
            aliases = load_profiles(draft, profiles)
            signature = (len(picks), str(draft.get("status") or ""), str(draft.get("last_picked") or ""))
            if signature != last_signature:
                candidates, round_no, next_ordinal = build_candidates(draft, picks, adp_by_id, adp_rows, profiles, aliases)
                result = None
                if MUSE_KEY and candidates:
                    try:
                        result = muse_select(model, candidates, history, round_no, next_ordinal)
                    except Exception as e:
                        print(f"Muse call failed; using deterministic ranking: {e}", flush=True)
                payload = assemble_analysis(draft_id, candidates, result, model if result else None, round_no, next_ordinal, history)
                publish_analysis(payload)
                last_signature = signature
            if str(draft.get("status") or "").lower() == "complete":
                print("Draft complete; AI watcher exiting.", flush=True)
                return
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"Draft {draft_id} not found; watcher exiting.", flush=True)
                return
            print(f"HTTP error {e.code}: {e}", flush=True)
        except Exception as e:
            print(f"Watcher iteration failed: {e}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
