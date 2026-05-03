# 🎵 Symphony — Fully automated pipeline

> Multi-agent coding pipeline. Fully free. Your only manual step: create an issue.

---

## Automation Level By Layer

| Layer | Component | Automated |
|---|---|---|
| Configuration | `AGENTS.md` | ✅ Always available |
| Trigger | Auto-label workflow + automatic label setup | ✅ Fully automatic |
| Orchestration | GitHub Actions | ✅ Fully automatic |
| Coding agent | `coding_agent.py` | ✅ Fully automatic |
| Review agent | `review_agent.py` | ✅ Fully automatic |
| Refinement | `retry_agent.py` (max 3x) | ✅ Fully automatic |
| Version control | Git + GitHub | ✅ Fully automatic |
| Completion | Auto-merge + issue done | ✅ Fully automatic |

**Your only manual step: create an issue.**

---

## The Full Loop

```
You create an issue
        ↓
Auto-label (immediately or within 15 minutes)
        ↓
Coding Agent writes code + opens PR
        ↓
Review Agent reviews diff
        ↓
    No issues?   → Auto-merge → Issue done
    Has issues?  → Retry Agent (max 3x)
                   → improves code
                   → Review Agent again
                   → after 3x: manual review
```

---

## Files

```
/
├── AGENTS.md                        ← Single source of truth
├── coding_agent.py                  ← Writes code + opens PR
├── review_agent.py                  ← Reviews PR
├── retry_agent.py                   ← Improves code after rejection
├── .github/
│   ├── workflows/
│   │   ├── auto-label.yml           ← Automatically labels new issues
│   │   ├── coding-agent.yml         ← Triggered by agent-ready label
│   │   └── review-agent.yml         ← Review + retry loop + auto-merge
│   ├── ISSUE_TEMPLATE/
│   │   └── agent-task.md
│   └── PULL_REQUEST_TEMPLATE.md
└── .vscode/
    └── tasks.json
```

---

## One-Time Setup (5 minutes)

### 1. Create a Groq API key (free)
Go to [console.groq.com](https://console.groq.com) and create an API key.

### 2. Add the secret
**Settings → Secrets and variables → Actions → New repository secret**
Name: `GROQ_API_KEY` · Value: your Groq key

### 3. Configure Actions permissions
**Settings → Actions → General → Workflow permissions**
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

### 4. Customize AGENTS.md
Update the tech stack, test command, and project structure for your project.

Labels are created or updated automatically by the workflows:
`agent-ready`, `in-progress`, `in-review`, `needs-work`, `symphony`, `symphony-approved`, `done`.

---

## Codex VS Code — After 3 Failed Retries

```
Ctrl+Shift+P → 🎵 Symphony: Open PRs
→ open the blocked PR in VS Code
→ start Codex in Agent (Full Access)
→ paste the review feedback
→ push → Review Agent triggers again
```
