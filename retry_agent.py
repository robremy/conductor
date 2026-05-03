#!/usr/bin/env python3
"""
Conductor — Retry Agent
Runs when the Review Agent blocks a PR.
Reads the review feedback and improves the implementation.
Max 3 retry attempts per issue.
"""

import os
import json
import subprocess
import requests
import re
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO         = os.environ["REPO"]
PR_NUMBER    = os.environ["PR_NUMBER"]
GITHUB_ENV   = os.environ.get("GITHUB_ENV", "/dev/null")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MAX_RETRIES  = 3

GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

EXCLUDED_DIRS = {".git", "node_modules", ".next", "dist", "build", "__pycache__"}
PROTECTED_DIRS = {".git"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg): print(msg, flush=True)

def gh_get(path):
    r = requests.get(f"https://api.github.com{path}", headers=GH_HEADERS)
    r.raise_for_status()
    return r.json()

def gh_post(path, body):
    r = requests.post(f"https://api.github.com{path}", headers=GH_HEADERS, json=body)
    r.raise_for_status()
    return r.json()

def set_gha_env(key, value):
    with open(GITHUB_ENV, "a") as f:
        f.write(f"{key}={value}\n")

def read_file(path):
    try:
        with open(path, encoding="utf-8") as f: return f.read()
    except FileNotFoundError: return ""

def get_current_files():
    """Read all relevant project files for context."""
    files = {}
    paths = []
    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name.startswith("_") and path.suffix == ".txt":
            continue
        paths.append(path)
    for path in sorted(paths)[:50]:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
                if len(content) < 5000:  # Only small files
                    files[path.as_posix()] = content
        except: pass
    return files

def get_retry_count():
    """Count how many retry comments are already on the PR."""
    comments = gh_get(f"/repos/{REPO}/issues/{PR_NUMBER}/comments")
    return sum(1 for c in comments if "Conductor Retry Agent" in c.get("body", ""))

def get_review_feedback():
    """Fetch review feedback from PR comments."""
    comments = gh_get(f"/repos/{REPO}/issues/{PR_NUMBER}/comments")
    for comment in reversed(comments):
        body = comment.get("body", "")
        if "Conductor Review Agent" in body and "CHANGES REQUESTED" in body:
            return body
    return ""

def call_groq(system_prompt, user_message, retries=5):
    import time
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": 8000,
        "temperature": 0.15,
    }
    for attempt in range(retries):
        r = requests.post(GROQ_URL, headers=headers, json=body)
        if r.status_code == 429:
            wait = 2 ** attempt
            log(f"⏳ Groq rate limit — waiting {wait}s (attempt {attempt + 1}/{retries})")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    raise RuntimeError("Groq rate limit — max retries reached")

def parse_json(raw):
    if "```" in raw:
        for part in raw.split("```"):
            candidate = part.strip().lstrip("json").strip()
            try: return json.loads(candidate)
            except: continue
    return json.loads(raw)

def safe_repo_path(raw_path):
    path = Path(str(raw_path).strip().lstrip("/\\"))
    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Invalid path from agent output: {raw_path}")
    if path.parts[0] in PROTECTED_DIRS:
        raise ValueError(f"Protected path may not be changed: {raw_path}")
    return path

def write_files(files):
    for f in files:
        path = safe_repo_path(f["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh: fh.write(f["content"])
        log(f"  ✓ {path}")

def run_tests(command):
    if not command: return True
    log(f"🧪 Tests: {command}")
    r = subprocess.run(command, shell=True, capture_output=True, text=True)
    if r.returncode == 0:
        log("  ✓ Tests passed")
        return True
    log(f"  ✗ Tests failed:\n{r.stdout[-500:]}")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("🔄 Retry Agent started")

    # Check retry count
    retry_count = get_retry_count()
    if retry_count >= MAX_RETRIES:
        log(f"❌ Maximum retries ({MAX_RETRIES}) reached")
        gh_post(f"/repos/{REPO}/issues/{PR_NUMBER}/comments", {
            "body": f"⛔ **Conductor Retry Agent**: Maximum of {MAX_RETRIES} retries reached.\n\nManual review required."
        })
        set_gha_env("RETRY_OK", "false")
        raise SystemExit(0)

    log(f"🔄 Retry attempt {retry_count + 1}/{MAX_RETRIES}")

    # Fetch PR
    pr = gh_get(f"/repos/{REPO}/pulls/{PR_NUMBER}")
    pr_title = pr["title"]
    pr_body  = pr.get("body") or ""

    # Fetch issue
    issue_title = ""
    issue_body  = ""
    match = re.search(r"Closes #(\d+)", pr_body, re.IGNORECASE)
    if match:
        try:
            issue = gh_get(f"/repos/{REPO}/issues/{match.group(1)}")
            issue_title = issue["title"]
            issue_body  = issue.get("body") or ""
        except: pass

    # Fetch review feedback
    review_feedback = get_review_feedback()
    if not review_feedback:
        log("No review feedback found — skip")
        set_gha_env("RETRY_OK", "false")
        raise SystemExit(0)

    log(f"📋 PR #{PR_NUMBER}: {pr_title}")

    # Read current files
    current_files = get_current_files()
    agents_md = read_file("AGENTS.md")

    system_prompt = f"""You are the Conductor Retry Agent.
You improve an existing implementation based on review feedback.

## AGENTS.md
{agents_md}

## Output Format
Return ONLY a valid JSON object. No markdown, no explanation.

{{
  "analysis": "What was wrong and how you fixed it",
  "files": [
    {{"path": "path/to/file.js", "content": "complete improved file contents"}}
  ],
  "test_command": "npm test",
  "commit_message": "fix: address review feedback\\n\\n- What was fixed\\n- Closes #NNN"
}}

Rules:
- Write COMPLETE file contents, including unchanged files
- Fix ALL blocking issues from the review
- Write tests for missing coverage
- No console.log or debug code"""

    current_files_str = "\n\n".join([
        f"### {path}\n```\n{content}\n```"
        for path, content in current_files.items()
    ])

    user_message = f"""Improve this implementation based on the review feedback.

**Issue:** {issue_title}
{issue_body}

**Current files:**
{current_files_str}

**Review feedback:**
{review_feedback}

Fix all blocking issues and return the JSON object."""

    log(f"🤖 Groq aanroepen ({GROQ_MODEL})...")
    raw = call_groq(system_prompt, user_message)

    try:
        result = parse_json(raw)
    except Exception as e:
        log(f"❌ JSON parse failed: {e}")
        set_gha_env("RETRY_OK", "false")
        raise SystemExit(1)

    log(f"🔍 {result.get('analysis', '—')}")
    write_files(result.get("files", []))
    tests_ok = run_tests(result.get("test_command"))

    commit_msg = result.get("commit_message", f"fix: address review feedback (retry {retry_count + 1})")
    with open("_commit_message.txt", "w", encoding="utf-8") as f: f.write(commit_msg)

    set_gha_env("RETRY_OK", "true" if tests_ok else "false")

    # Comment on PR
    gh_post(f"/repos/{REPO}/issues/{PR_NUMBER}/comments", {
        "body": f"🔄 **Conductor Retry Agent** (attempt {retry_count + 1}/{MAX_RETRIES})\n\n"
                f"**Analysis:** {result.get('analysis', '—')}\n\n"
                f"**Tests:** {'✅ passed' if tests_ok else '⚠️ failed'}\n\n"
                f"Review Agent will be triggered again."
    })

    log("✅ Retry Agent done")

if __name__ == "__main__":
    main()
