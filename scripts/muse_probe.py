#!/usr/bin/env python3
import base64
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://api.meta.ai/v1"
KEY = os.environ.get("MUSE_API_KEY", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "wlatic/draft-center")
BRANCH = os.environ.get("ANALYSIS_BRANCH", "analysis")


def request_json(url, method="GET", body=None):
    headers = {"Accept": "application/json", "User-Agent": "DraftCenter-Muse-Probe"}
    if KEY:
        headers["Authorization"] = f"Bearer {KEY}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")[:500]
        try:
            parsed = json.loads(raw)
            msg = parsed.get("message") or parsed.get("error") or raw
        except Exception:
            msg = raw
        return e.code, {"error": str(msg)[:300]}
    except Exception as e:
        return 0, {"error": f"{type(e).__name__}: {e}"[:300]}


def publish(payload):
    if not TOKEN:
        return
    path = "muse-probe.json"
    api = f"https://api.github.com/repos/{REPO}/contents/{path}"
    gh_headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "DraftCenter-Muse-Probe",
    }
    sha = None
    try:
        req = urllib.request.Request(f"{api}?ref={BRANCH}", headers=gh_headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            sha = json.loads(r.read().decode()).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    body = {
        "message": "Update Muse API probe",
        "content": base64.b64encode((json.dumps(payload, indent=2) + "\n").encode()).decode(),
        "branch": BRANCH,
    }
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(api, data=json.dumps(body).encode(), headers=gh_headers, method="PUT")
    with urllib.request.urlopen(req, timeout=20):
        pass


result = {
    "updatedAt": datetime.now(timezone.utc).isoformat(),
    "secretPresent": bool(KEY),
    "models": [],
    "tests": {},
}

if KEY:
    status, data = request_json(BASE + "/models")
    result["modelsStatus"] = status
    if status == 200:
        result["models"] = [str(x.get("id")) for x in data.get("data", []) if "muse" in str(x.get("id", "")).lower()]
    else:
        result["modelsError"] = data.get("error", "unknown")

    for model in ("muse-spark-1.3-contributor", "muse-spark-1.3"):
        status, data = request_json(BASE + "/chat/completions", "POST", {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly OK"}],
            "max_tokens": 16,
            "reasoning_effort": "minimal",
        })
        test = {"status": status}
        if status == 200:
            try:
                test["ok"] = bool(data.get("choices"))
            except Exception:
                test["ok"] = True
        else:
            test["error"] = data.get("error", "unknown")
        result["tests"][model] = test

print(json.dumps(result, indent=2), flush=True)
publish(result)
