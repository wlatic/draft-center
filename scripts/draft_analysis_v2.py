#!/usr/bin/env python3
import json
import re

import draft_analysis as core


def discover_model():
    # The repo's safe probe verifies this exact model with the MUSE Actions
    # secret before the watcher starts. Keep the live desk on contributor tier.
    return "muse-spark-1.3-contributor" if core.MUSE_KEY else None


def muse_select(model, candidates, history, round_no, next_ordinal):
    if not core.MUSE_KEY or not model or not candidates:
        return None

    compact = [{k: f[k] for k in ("id", "title", "detail", "score")} for f in candidates]
    prompt = {
        "job": "You are the editorial producer for a live fantasy-football DraftCenter TV desk.",
        "round": round_no,
        "nextOverallPick": next_ordinal,
        "recentFactIds": history[-16:],
        "rules": [
            "Pick exactly four supplied fact IDs, or fewer only if fewer facts exist.",
            "Prefer what is surprising, timely, useful, funny, or tells a developing draft story.",
            "Avoid recently used fact IDs when comparable fresh facts exist.",
            "Never invent or alter a number, player, manager, team, ADP, position count, cause, or strategy.",
            "For each selection you may add one personality-only take of at most twelve words.",
            "A take may not contain digits or make a new factual claim.",
            "Return JSON only: {\"headline\":\"...\",\"selections\":[{\"id\":\"...\",\"take\":\"...\"}]}",
        ],
        "facts": compact,
    }

    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Be a sharp, concise fantasy-football studio producer. Use only supplied fact IDs. Output JSON only.",
            },
            {"role": "user", "content": json.dumps(prompt, separators=(",", ":"))},
        ],
        "max_tokens": 700,
        "temperature": 0.45,
        "reasoning_effort": "minimal",
        "response_format": {"type": "json_object"},
    }

    data = core.http_json(
        core.META_API + "/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {core.MUSE_KEY}"},
        body=body,
        timeout=45,
    )
    message = (((data or {}).get("choices") or [{}])[0].get("message") or {})
    text = message.get("content") or ""
    if isinstance(text, list):
        text = "".join(str(x.get("text") or "") if isinstance(x, dict) else str(x) for x in text)
    text = str(text).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Be tolerant of a small amount of prose despite JSON-mode instructions.
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


core.discover_model = discover_model
core.muse_select = muse_select

if __name__ == "__main__":
    core.main()
