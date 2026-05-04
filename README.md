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

## Layer Status and Testing

### 1. Configuration
**Component:** `AGENTS.md`  
**Status:** File exists but requires customization for target project stack, structure, and test commands.  
**Test Plan:** Manually review AGENTS.md content and verify it matches the project's requirements. Run a syntax check if applicable.

### 2. Trigger
**Component:** Auto-label workflow + automatic label setup  
**Status:** Workflow files exist, but GitHub Actions permissions need to be enabled for read/write and PR approvals.  
**Test Plan:** Create a test issue and verify it gets automatically labeled with "agent-ready" within 15 minutes.

### 3. Orchestration
**Component:** GitHub Actions  
**Status:** Workflows are configured and present.  
**Test Plan:** Check workflow run history in GitHub Actions tab to ensure workflows can be triggered.

### 4. Coding Agent
**Component:** `coding_agent.py`  
**Status:** Code implemented and ready.  
**Test Plan:** Trigger the coding agent workflow manually (if possible) or via a labeled issue, and verify it generates code and opens a PR.

### 5. Review Agent
**Component:** `review_agent.py`  
**Status:** Code implemented and ready.  
**Test Plan:** After a PR is opened by the coding agent, verify the review agent runs and provides feedback or approves.

### 6. Refinement
**Component:** `retry_agent.py` (max 3x)  
**Status:** Code implemented with retry logic.  
**Test Plan:** Force a review rejection and verify the retry agent improves the code up to 3 times before stopping.

### 7. Version Control
**Component:** Git + GitHub  
**Status:** Repository is set up with Git.  
**Test Plan:** Verify commits, branches, and pushes work correctly during the pipeline execution.

### 8. Completion
**Component:** Auto-merge + issue done  
**Status:** Auto-merge settings need verification to match workflow expectations.  
**Test Plan:** Ensure a successfully reviewed PR auto-merges and closes the original issue.

---

## Getting Started with a Project Idea

When you have only a project idea and no existing codebase:

### 1. Create a New Repository
- Create a new GitHub repository for your project
- Clone it to your local machine

### 2. Add Conductor Workflow
- Copy the `.github/workflows/` directory from this Conductor repository to your new project
- This enables the automated pipeline

### 3. Create Your First Issue
- Open a GitHub issue describing your initial feature or component
- Label it with `agent-ready` (or wait for auto-labeling)
- Conductor will detect missing components and prompt you to add them:
  - **AGENTS.md**: Project configuration (created automatically with guidance)
  - **GROQ_API_KEY**: API key for AI processing (setup instructions provided)
  - **Permissions**: GitHub Actions permissions (configuration steps given)

### 4. Follow the Prompts
- When Conductor identifies missing requirements, follow the issue comments
- Each prompt provides specific instructions for the missing component
- No upfront setup required - everything is guided on-demand

### 5. Iterate
- Create additional issues for new features
- The pipeline handles coding, testing, and merging automatically
- Manual intervention only for complex requirements or after 3 failed retries

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

## Testing Conductor

### Startup Test
Test the Conductor initialization and prompting system locally:

```bash
python test_startup.py
```

This script simulates:
- ✅ API key validation
- ✅ Required file checks (AGENTS.md)
- ✅ Project type detection (new vs existing)
- ✅ Prompt generation for missing components

### Test Scenarios
- **Normal operation**: All checks pass, shows code generation would proceed
- **Missing API key**: Shows the guidance prompt for setting up GROQ_API_KEY
- **Missing AGENTS.md**: Shows the template and instructions for project configuration
- **New project**: Would detect empty repo and generate initial structure

---

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

## One-Time Setup (Optional - Guided Setup Available)

Conductor can be set up automatically when you first use it. However, for a smoother experience, you can pre-configure these settings:

### Automated Setup (Recommended)

Run the automated setup script:

```powershell
# From your project root (where Conductor workflows are copied)
.\setup_conductor.ps1
```

This script will:
- ✅ Check GitHub CLI installation and authentication
- ✅ Open Groq console in your browser
- ✅ Guide you through API key creation
- ✅ Automatically set the `GROQ_API_KEY` secret
- ✅ Configure GitHub Actions permissions
- ✅ Verify repository setup

### Guided Setup (On-Demand)

If you prefer minimal upfront setup:
- Just copy the `.github/workflows/` directory
- Create your first issue
- Follow the prompts in issue comments for any missing requirements

### Manual Setup (Alternative)

#### 1. Create a Groq API key (free)
Go to [console.groq.com](https://console.groq.com) and create an API key.

#### 2. Add the secret
**Settings → Secrets and variables → Actions → New repository secret**
Name: `GROQ_API_KEY` · Value: your Groq key

#### 3. Configure Actions permissions
**Settings → Actions → General → Workflow permissions**
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

#### 4. Customize AGENTS.md
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
