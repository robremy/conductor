#!/usr/bin/env python3
"""
Conductor — Review Agent
Reads a PR diff, reviews it using the AGENTS.md review criteria,
and decides whether auto-merge is allowed.
"""

import os
import json
import requests

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO         = os.environ["REPO"]
PR_NUMBER    = os.environ["PR_NUMBER"]
GITHUB_ENV   = os.environ.get("GITHUB_ENV", "/dev/null")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
TESTS_PASS   = os.environ.get("TESTS_PASS", "true").lower() == "true"

GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

GH_DIFF_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.diff",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg): print(msg, flush=True)

def gh_get(path, headers=None):
    r = requests.get(f"https://api.github.com{path}", headers=headers or GH_HEADERS)
    r.raise_for_status()
    return r.json()

def gh_get_raw(path):
    r = requests.get(f"https://api.github.com{path}", headers=GH_DIFF_HEADERS)
    r.raise_for_status()
    return r.text

def gh_post(path, body):
    r = requests.post(f"https://api.github.com{path}", headers=GH_HEADERS, json=body)
    r.raise_for_status()
    return r.json()

def gh_put(path, body):
    r = requests.put(f"https://api.github.com{path}", headers=GH_HEADERS, json=body)
    r.raise_for_status()
    return r.json()

def set_gha_env(key, value):
    with open(GITHUB_ENV, "a") as f:
        f.write(f"{key}={value}\n")

def read_file(path):
    try:
        with open(path) as f: return f.read()
    except FileNotFoundError: return ""

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
        "max_tokens": 3000,
        "temperature": 0.1,
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

def add_pr_label(label):
    try:
        gh_post(f"/repos/{REPO}/issues/{PR_NUMBER}/labels", {"labels": [label]})
    except: pass

def remove_pr_label(label):
    try:
        requests.delete(
            f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/labels/{label}",
            headers=GH_HEADERS
        )
    except: pass

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("🔍 Review Agent started")

    # Fetch PR
    pr = gh_get(f"/repos/{REPO}/pulls/{PR_NUMBER}")
    pr_title = pr["title"]
    pr_body  = pr.get("body") or ""
    base_sha = pr["base"]["sha"]
    head_sha = pr["head"]["sha"]

    log(f"📋 PR #{PR_NUMBER}: {pr_title}")

    # Fetch diff (max 8000 characters)
    diff = gh_get_raw(f"/repos/{REPO}/pulls/{PR_NUMBER}")
    diff_truncated = diff[:8000]
    if len(diff) > 8000:
        diff_truncated += "\n\n[diff truncated — too long]"

    # Fetch issue via PR body (look for "Closes #NNN")
    issue_body = ""
    issue_title = ""
    import re
    match = re.search(r"Closes #(\d+)", pr_body, re.IGNORECASE)
    if match:
        issue_num = match.group(1)
        try:
            issue = gh_get(f"/repos/{REPO}/issues/{issue_num}")
            issue_title = issue["title"]
            issue_body  = issue.get("body") or ""
            log(f"🔗 Linked issue: #{issue_num} — {issue_title}")
        except: pass

    # Read AGENTS.md
    agents_md = read_file("AGENTS.md")

    system_prompt = f"""You are the Conductor Review Agent.
You review a Pull Request based on the review criteria in AGENTS.md.

## AGENTS.md (the review criteria section is the most important)
{agents_md}

## Output Format
Return ONLY a valid JSON object. No markdown, no explanation.

{{
  "blocking_issues": [
    "Description of blocking problem (empty if none)"
  ],
  "non_blocking_remarks": [
    "Non-blocking remark (empty if none)"
  ],
  "auto_merge": true,
  "summary": "Brief review summary in English",
  "verdict": "APPROVED" or "CHANGES_REQUESTED"
}}

Rules:
- auto_merge is true ONLY when there are no blocking issues
- Be strict about failing tests, missing tests, and bugs
- Be mild about style preferences and small optimizations
- If the diff is too small for the issue scope, that is a blocking issue"""

    user_message = f"""Review this Pull Request:

**PR #{PR_NUMBER}: {pr_title}**

**Original issue:**
{issue_title}
{issue_body}

**PR description:**
{pr_body}

**CI tests:**
{"Passed" if TESTS_PASS else "Failed"}

**Diff:**
```diff
{diff_truncated}
```

Review based on the AGENTS.md review criteria and return the JSON object."""

    log(f"🤖 Groq aanroepen ({GROQ_MODEL})...")
    raw = call_groq(system_prompt, user_message)

    try:
        result = parse_json(raw)
    except Exception as e:
        log(f"❌ JSON parse failed: {e}")
        gh_post(f"/repos/{REPO}/issues/{PR_NUMBER}/comments", {
            "body": f"⚠️ Review Agent could not parse the output. Manual review required.\n\n```\n{raw[:500]}\n```"
        })
        set_gha_env("AUTO_MERGE", "false")
        raise SystemExit(1)

    blocking    = result.get("blocking_issues", [])
    non_blocking = result.get("non_blocking_remarks", [])
    auto_merge  = result.get("auto_merge", False)
    summary     = result.get("summary", "—")
    verdict     = result.get("verdict", "CHANGES_REQUESTED")

    if not TESTS_PASS:
        blocking.append("The CI tests failed in the GitHub Actions run.")
        auto_merge = False
        verdict = "CHANGES_REQUESTED"

    log(f"📊 Verdict: {verdict}")
    log(f"🚦 Auto-merge: {auto_merge}")
    log(f"🔴 Blocking issues: {len(blocking)}")
    log(f"🟡 Remarks: {len(non_blocking)}")

    # Compose PR comment
    comment_lines = [
        f"## 🎛️ Conductor Review Agent\n",
        f"**Verdict:** {'✅ APPROVED' if verdict == 'APPROVED' else '❌ CHANGES REQUESTED'}\n",
        f"**Auto-merge:** {'✅ Yes' if auto_merge else '❌ No'}\n",
        f"### Summary\n{summary}\n",
    ]

    if blocking:
        comment_lines.append("### 🔴 Blocking Issues\n")
        for b in blocking:
            comment_lines.append(f"- {b}")
        comment_lines.append("")

    if non_blocking:
        comment_lines.append("### 🟡 Remarks (non-blocking)\n")
        for r in non_blocking:
            comment_lines.append(f"- {r}")
        comment_lines.append("")

    if auto_merge:
        comment_lines.append("---\n✅ No blocking issues found. PR will be merged automatically.")
    else:
        comment_lines.append("---\n❌ Blocking issues found. Auto-merge delayed. Fix the issues and push an update.")

    gh_post(f"/repos/{REPO}/issues/{PR_NUMBER}/comments", {
        "body": "\n".join(comment_lines)
    })

    # Update labels
    if auto_merge:
        add_pr_label("conductor-approved")
        remove_pr_label("needs-work")
    else:
        add_pr_label("needs-work")
        remove_pr_label("conductor-approved")

    set_gha_env("AUTO_MERGE", "true" if auto_merge else "false")
    log("✅ Review Agent done")

if __name__ == "__main__":
    main()
