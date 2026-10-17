#!/usr/bin/env python3
import json
import os
import urllib.request
import urllib.parse
import urllib.error
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
RESP_PATH = os.path.join(REPO_ROOT, "responsibilities.json")
OUTPUT_PATH = os.path.join(REPO_ROOT, "commits.json")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

with open(RESP_PATH, "r", encoding="utf-8") as f:
    resp_data = json.load(f)

commits_map = {}

headers = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "DEOS-Commit-Updater"
}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

for comp in resp_data.get("components", []):
    comp_id = comp.get("id")
    repo = comp.get("repo")
    path = comp.get("path")
    if not repo:
        continue

    url = f"https://api.github.com/repos/{repo}/commits?per_page=1"
    if path:
        url += f"&path={urllib.parse.quote(path)}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data and isinstance(data, list) and len(data) > 0:
                c = data[0]
                sha = c.get("sha", "")[:7]
                author = (c.get("commit", {}).get("author", {}) or {}).get("name") or (c.get("author", {}) or {}).get("login") or "Bilinmiyor"
                msg = (c.get("commit", {}).get("message") or "").split("\n")[0]
                raw_date = (c.get("commit", {}).get("author", {}) or {}).get("date")
                
                commits_map[comp_id] = {
                    "hash": sha,
                    "author": author,
                    "msg": msg,
                    "date": raw_date or ""
                }
                print(f"[{comp_id}] {sha} ({author}): {msg} @ {raw_date}")
    except Exception as e:
        print(f"[{comp_id}] Error fetching commit: {e}")

output_data = {
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "commits": commits_map
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Saved {len(commits_map)} commits to {OUTPUT_PATH}")
