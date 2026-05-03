# 🎛️ Conductor — Fully automated pipeline

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

## Done

- [x] Added `AGENTS.md` as the shared instruction source for coding and review.
- [x] Added issue and pull request templates for agent-driven work.
- [x] Added automatic Conductor label setup.
- [x] Added issue auto-labeling with `agent-ready`.
- [x] Added Coding Agent workflow to generate changes, commit them, push a branch, open a PR, and trigger review.
- [x] Added Review Agent workflow with PR review, test awareness, auto-merge, retry dispatch, and issue completion.
- [x] Added Retry Agent workflow path with a maximum of 3 attempts.
- [x] Added VS Code tasks for triggering and inspecting Conductor work.
- [x] Translated project documentation and agent-facing text to English.

## ToDo

- [ ] Add `GROQ_API_KEY` as a repository Actions secret.
- [ ] Enable GitHub Actions read/write workflow permissions and PR approval permissions.
- [ ] Customize `AGENTS.md` for the target project stack, structure, and test command.
- [ ] Run the first end-to-end test with a small issue.
- [ ] Verify repository auto-merge settings match the workflow expectations.
- [ ] Add workflow linting, for example with `actionlint`, to catch YAML or GitHub expression issues.
- [ ] Consider replacing `GITHUB_TOKEN` with a GitHub App or PAT if stricter workflow-trigger behavior is needed.
- [ ] Review security boundaries before using the pipeline on sensitive repositories.

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
├── .gitignore                       ← Ignores generated local files
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
`agent-ready`, `in-progress`, `in-review`, `needs-work`, `conductor`, `conductor-approved`, `done`.

---

## Codex VS Code — After 3 Failed Retries

```
Ctrl+Shift+P → 🎛️ Conductor: Open PRs
→ open the blocked PR in VS Code
→ start Codex in Agent (Full Access)
→ paste the review feedback
→ push → Review Agent triggers again
```
