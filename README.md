# 🎵 Symphony — Volledig geautomatiseerde pipeline

> Multi-agent coding pipeline. Volledig gratis. Jouw enige handmatige stap: een issue aanmaken.

---

## Automatiseringsgraad per laag

| Laag | Component | Geautomatiseerd |
|---|---|---|
| Configuratie | `AGENTS.md` | ✅ Altijd beschikbaar |
| Trigger | Auto-label workflow + automatische label setup | ✅ Volledig automatisch |
| Orkestratie | GitHub Actions | ✅ Volledig automatisch |
| Coding agent | `coding_agent.py` | ✅ Volledig automatisch |
| Review agent | `review_agent.py` | ✅ Volledig automatisch |
| Verfijning | `retry_agent.py` (max 3x) | ✅ Volledig automatisch |
| Versiecontrole | Git + GitHub | ✅ Volledig automatisch |
| Afsluiting | Auto-merge + issue done | ✅ Volledig automatisch |

**Jouw enige handmatige stap: een issue aanmaken.**

---

## De volledige loop

```
Jij maakt issue aan
        ↓
Auto-label (direct of binnen 15 min)
        ↓
Coding Agent schrijft code + opent PR
        ↓
Review Agent beoordeelt diff
        ↓
    Geen issues? → Auto-merge → Issue done
    Wel issues?  → Retry Agent (max 3x)
                   → verbetert code
                   → Review Agent opnieuw
                   → na 3x: handmatige review
```

---

## Bestanden

```
/
├── AGENTS.md                        ← Single source of truth
├── coding_agent.py                  ← Schrijft code + opent PR
├── review_agent.py                  ← Beoordeelt PR
├── retry_agent.py                   ← Verbetert code na afwijzing
├── .github/
│   ├── workflows/
│   │   ├── auto-label.yml           ← Labelt nieuwe issues automatisch
│   │   ├── coding-agent.yml         ← Triggered op label agent-ready
│   │   └── review-agent.yml         ← Review + retry loop + auto-merge
│   ├── ISSUE_TEMPLATE/
│   │   └── agent-task.md
│   └── PULL_REQUEST_TEMPLATE.md
└── .vscode/
    └── tasks.json
```

---

## Eenmalige setup (5 minuten)

### 1. Groq API key aanmaken (gratis)
Ga naar [console.groq.com](https://console.groq.com) en maak een API key aan.

### 2. Secret toevoegen
**Settings → Secrets and variables → Actions → New repository secret**
Naam: `GROQ_API_KEY` · Waarde: jouw Groq key

### 3. Actions rechten instellen
**Settings → Actions → General → Workflow permissions**
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

### 4. AGENTS.md aanpassen
Pas techstack, testcommando en projectstructuur aan op jouw project.

Labels worden automatisch aangemaakt of bijgewerkt door de workflows:
`agent-ready`, `in-progress`, `in-review`, `needs-work`, `symphony`, `symphony-approved`, `done`.

---

## Codex VS Code — na 3 mislukte retries

```
Ctrl+Shift+P → 🎵 Symphony: Open PRs
→ open geblokkeerde PR in VS Code
→ start Codex in Agent (Full Access)
→ plak de review feedback
→ push → Review Agent triggert opnieuw
```
