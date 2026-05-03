#!/usr/bin/env python3
"""
Symphony — Review Agent
Leest een PR diff, beoordeelt op basis van AGENTS.md review criteria,
besluit of auto-merge toegestaan is.
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
            log(f"⏳ Groq rate limit — wacht {wait}s (poging {attempt + 1}/{retries})")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    raise RuntimeError("Groq rate limit — max retries bereikt")

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
    log("🔍 Review Agent gestart")

    # PR ophalen
    pr = gh_get(f"/repos/{REPO}/pulls/{PR_NUMBER}")
    pr_title = pr["title"]
    pr_body  = pr.get("body") or ""
    base_sha = pr["base"]["sha"]
    head_sha = pr["head"]["sha"]

    log(f"📋 PR #{PR_NUMBER}: {pr_title}")

    # Diff ophalen (max 8000 tekens)
    diff = gh_get_raw(f"/repos/{REPO}/pulls/{PR_NUMBER}")
    diff_truncated = diff[:8000]
    if len(diff) > 8000:
        diff_truncated += "\n\n[diff ingekort — te lang]"

    # Issue ophalen via PR body (zoek "Closes #NNN")
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
            log(f"🔗 Gekoppeld issue: #{issue_num} — {issue_title}")
        except: pass

    # AGENTS.md lezen
    agents_md = read_file("AGENTS.md")

    system_prompt = f"""Je bent Symphony Review Agent.
Je beoordeelt een Pull Request op basis van de review criteria in AGENTS.md.

## AGENTS.md (review criteria sectie is het belangrijkst)
{agents_md}

## Outputformaat
Geef UITSLUITEND een geldig JSON-object terug. Geen markdown, geen uitleg.

{{
  "blocking_issues": [
    "Beschrijving van blokkerend probleem (leeg als geen)"
  ],
  "non_blocking_remarks": [
    "Niet-blokkerende opmerking (leeg als geen)"
  ],
  "auto_merge": true,
  "summary": "Korte samenvatting van de review in het Nederlands",
  "verdict": "APPROVED" of "CHANGES_REQUESTED"
}}

Regels:
- auto_merge is true ALLEEN als er geen blokkerende issues zijn
- Wees streng op falende tests, ontbrekende tests en bugs
- Wees mild op stijlvoorkeuren en kleine optimalisaties
- Als de diff te kort is voor de scope van het issue, is dat een blokkerend issue"""

    user_message = f"""Review deze Pull Request:

**PR #{PR_NUMBER}: {pr_title}**

**Origineel issue:**
{issue_title}
{issue_body}

**PR beschrijving:**
{pr_body}

**CI tests:**
{"Geslaagd" if TESTS_PASS else "Mislukt"}

**Diff:**
```diff
{diff_truncated}
```

Beoordeel op basis van AGENTS.md review criteria en lever het JSON-object op."""

    log(f"🤖 Groq aanroepen ({GROQ_MODEL})...")
    raw = call_groq(system_prompt, user_message)

    try:
        result = parse_json(raw)
    except Exception as e:
        log(f"❌ JSON parse mislukt: {e}")
        gh_post(f"/repos/{REPO}/issues/{PR_NUMBER}/comments", {
            "body": f"⚠️ Review Agent kon output niet parsen. Handmatige review vereist.\n\n```\n{raw[:500]}\n```"
        })
        set_gha_env("AUTO_MERGE", "false")
        raise SystemExit(1)

    blocking    = result.get("blocking_issues", [])
    non_blocking = result.get("non_blocking_remarks", [])
    auto_merge  = result.get("auto_merge", False)
    summary     = result.get("summary", "—")
    verdict     = result.get("verdict", "CHANGES_REQUESTED")

    if not TESTS_PASS:
        blocking.append("De CI-tests zijn mislukt in de GitHub Actions run.")
        auto_merge = False
        verdict = "CHANGES_REQUESTED"

    log(f"📊 Verdict: {verdict}")
    log(f"🚦 Auto-merge: {auto_merge}")
    log(f"🔴 Blokkerende issues: {len(blocking)}")
    log(f"🟡 Opmerkingen: {len(non_blocking)}")

    # PR comment samenstellen
    comment_lines = [
        f"## 🎵 Symphony Review Agent\n",
        f"**Verdict:** {'✅ APPROVED' if verdict == 'APPROVED' else '❌ CHANGES REQUESTED'}\n",
        f"**Auto-merge:** {'✅ Ja' if auto_merge else '❌ Nee'}\n",
        f"### Samenvatting\n{summary}\n",
    ]

    if blocking:
        comment_lines.append("### 🔴 Blokkerende issues\n")
        for b in blocking:
            comment_lines.append(f"- {b}")
        comment_lines.append("")

    if non_blocking:
        comment_lines.append("### 🟡 Opmerkingen (niet-blokkerend)\n")
        for r in non_blocking:
            comment_lines.append(f"- {r}")
        comment_lines.append("")

    if auto_merge:
        comment_lines.append("---\n✅ Geen blokkerende issues gevonden. PR wordt automatisch gemerged.")
    else:
        comment_lines.append("---\n❌ Blokkerende issues gevonden. Auto-merge uitgesteld. Los de issues op en push een update.")

    gh_post(f"/repos/{REPO}/issues/{PR_NUMBER}/comments", {
        "body": "\n".join(comment_lines)
    })

    # Labels updaten
    if auto_merge:
        add_pr_label("symphony-approved")
        remove_pr_label("needs-work")
    else:
        add_pr_label("needs-work")
        remove_pr_label("symphony-approved")

    set_gha_env("AUTO_MERGE", "true" if auto_merge else "false")
    log("✅ Review Agent klaar")

if __name__ == "__main__":
    main()
