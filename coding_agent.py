#!/usr/bin/env python3
"""
Conductor — Coding Agent
Reads a GitHub Issue, writes the implementation, and opens a PR.
"""

import os
import json
import subprocess
import requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO         = os.environ["REPO"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
GITHUB_ENV   = os.environ.get("GITHUB_ENV", "/dev/null")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

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

def comment(msg):
    gh_post(f"/repos/{REPO}/issues/{ISSUE_NUMBER}/comments", {"body": msg})

def read_file(path):
    try:
        with open(path, encoding="utf-8") as f: return f.read()
    except FileNotFoundError: return ""

def get_repo_structure():
    lines = []
    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        lines.append(path.as_posix())
    lines = sorted(lines)
    return "\n".join(lines[:200])

def set_gha_env(key, value):
    with open(GITHUB_ENV, "a") as f:
        f.write(f"{key}={value}\n")

def slugify(text):
    slug = text.lower().replace(" ", "-")[:40]
    slug = "".join(c for c in slug if c.isalnum() or c == "-").strip("-")
    return slug or "task"

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
            wait = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
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
    log(f"  ✗ Tests failed:\n{r.stdout[-1000:]}\n{r.stderr[-500:]}")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("🎛️ Coding Agent started")

    issue  = gh_get(f"/repos/{REPO}/issues/{ISSUE_NUMBER}")
    title  = issue["title"]
    body   = issue.get("body") or "(no description)"
    branch = f"feat/GH-{ISSUE_NUMBER}-{slugify(title)}"

    log(f"📋 Issue #{ISSUE_NUMBER}: {title}")
    comment(f"🎛️ **Conductor Coding Agent started**\n\nProcessing issue `#{ISSUE_NUMBER}`.\nI will open a PR when the implementation is ready.")

    agents_md = read_file("AGENTS.md")
    structure = get_repo_structure()

    system_prompt = f"""You are Conductor, an autonomous coding agent.
You implement GitHub Issues fully and independently.

## Project Instructions (AGENTS.md)
{agents_md}

## Repository Structure
{structure}

## Output Format
Return ONLY a valid JSON object. No markdown, no explanation, no backticks.

{{
  "analysis": "Brief analysis of what needs to be built",
  "files": [
    {{"path": "path/to/file.js", "content": "complete file contents"}}
  ],
  "test_command": "npm test",
  "commit_message": "feat(GH-{ISSUE_NUMBER}): description\\n\\n- What changed\\n- Closes #{ISSUE_NUMBER}",
  "pr_title": "feat(GH-{ISSUE_NUMBER}): description",
  "pr_body": "## What does this PR do?\\n...\\n\\n## Testing\\n...\\n\\nCloses #{ISSUE_NUMBER}"
}}

Rules:
- Write COMPLETE file contents
- Follow the workflow in AGENTS.md exactly
- Only change files that are needed
- Write tests for new logic
- No console.log or debug code"""

    user_message = f"""Implement GitHub Issue #{ISSUE_NUMBER} fully.

**{title}**

{body}

Return the JSON object."""

    log(f"🤖 Groq aanroepen ({GROQ_MODEL})...")
    raw = call_groq(system_prompt, user_message)

    try:
        result = parse_json(raw)
    except Exception as e:
        log(f"❌ JSON parse failed: {e}")
        comment(f"❌ Coding Agent could not parse the output.\n\n```\n{raw[:500]}\n```")
        raise SystemExit(1)

    log(f"🔍 {result.get('analysis', '—')}")
    log(f"📝 {len(result.get('files', []))} bestanden")

    write_files(result.get("files", []))
    tests_ok = run_tests(result.get("test_command"))

    commit_msg = result.get("commit_message", f"feat(GH-{ISSUE_NUMBER}): {title}\n\nCloses #{ISSUE_NUMBER}")
    pr_title   = result.get("pr_title",   f"feat(GH-{ISSUE_NUMBER}): {title}")
    pr_body    = result.get("pr_body",    f"Implementation of #{ISSUE_NUMBER}.\n\nCloses #{ISSUE_NUMBER}")

    if not tests_ok:
        pr_body += "\n\n> ⚠️ Tests failed during the agent run. Review carefully."

    with open("_commit_message.txt", "w", encoding="utf-8") as f: f.write(commit_msg)
    with open("_pr_title.txt",       "w", encoding="utf-8") as f: f.write(pr_title)
    with open("_pr_body.txt",        "w", encoding="utf-8") as f: f.write(pr_body)

    set_gha_env("BRANCH_NAME", branch)
    set_gha_env("TESTS_OK", "true" if tests_ok else "false")

    log(f"🌿 Branch: {branch}")
    log("✅ Coding Agent done")

if __name__ == "__main__":
    main()
