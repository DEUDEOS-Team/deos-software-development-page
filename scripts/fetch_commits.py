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
LOCAL_FIRMWARE_RESP = "/home/emir/zephyrproject/applications/deos_firmware/responsibilities.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

def sync_responsibilities():
    """Sync responsibilities.json from deos-firmware (Single Source of Truth)."""
    # 1. Local path check (fastest and most up-to-date in local workspace)
    if os.path.exists(LOCAL_FIRMWARE_RESP):
        try:
            with open(LOCAL_FIRMWARE_RESP, "r", encoding="utf-8") as f:
                content = f.read()
                data = json.loads(content)
                if data and "components" in data and len(data["components"]) > 0:
                    with open(RESP_PATH, "w", encoding="utf-8") as out:
                        out.write(content if content.endswith("\n") else content + "\n")
                    print(f"Successfully synced from local deos-firmware ({len(data['components'])} components).")
                    return data
        except Exception as e:
            print(f"Note: Could not read local firmware file ({e}). Trying remote...")

    # 2. Remote check via GitHub API (used in GitHub Actions CI/CD)
    api_url = "https://api.github.com/repos/DEUDEOS-Team/deos-firmware/contents/responsibilities.json?ref=main"
    api_headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "DEOS-Sync"
    }
    if GITHUB_TOKEN:
        api_headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        req = urllib.request.Request(api_url, headers=api_headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode("utf-8")
            data = json.loads(content)
            if data and "components" in data and len(data["components"]) >= 15:
                with open(RESP_PATH, "w", encoding="utf-8") as out:
                    out.write(content if content.endswith("\n") else content + "\n")
                print(f"Successfully synced responsibilities.json via GitHub API from deos-firmware ({len(data['components'])} components).")
                return data
    except Exception as e:
        print(f"Note: GitHub API sync failed ({e}). Trying raw URL...")

    # 3. Fallback to raw.githubusercontent.com
    raw_url = "https://raw.githubusercontent.com/DEUDEOS-Team/deos-firmware/main/responsibilities.json"
    raw_headers = {"User-Agent": "DEOS-Sync"}
    if GITHUB_TOKEN:
        raw_headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        req = urllib.request.Request(raw_url, headers=raw_headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode("utf-8")
            data = json.loads(content)
            if data and "components" in data and len(data["components"]) >= 15:
                with open(RESP_PATH, "w", encoding="utf-8") as out:
                    out.write(content if content.endswith("\n") else content + "\n")
                print(f"Successfully synced responsibilities.json via raw CDN from deos-firmware ({len(data['components'])} components).")
                return data
    except Exception as e:
        print(f"Warning: Could not fetch from raw CDN ({e}). Using existing local file.")

    # 4. Fallback to existing local responsibilities.json
    if os.path.exists(RESP_PATH):
        with open(RESP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"components": []}

resp_data = sync_responsibilities()

# Load existing commits to preserve cache if API rate limits occur
existing_commits = {}
if os.path.exists(OUTPUT_PATH):
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            existing_commits = json.load(f).get("commits", {})
    except Exception:
        existing_commits = {}

commits_map = dict(existing_commits)

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
