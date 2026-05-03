# AGENTS.md
# Single source of truth voor coding agent én review agent.
# Wordt automatisch gelezen door beide GitHub Actions workflows.

---

## Project

Full-stack web applicatie.

## Techstack

<!-- Pas aan op jouw project -->
- **Frontend**: React / Vue / Svelte
- **Backend**: Node/Express / FastAPI / Laravel
- **Database**: PostgreSQL / MongoDB
- **Tests**: Vitest / Jest / Pytest
- **Package manager**: npm / pnpm / pip

## Projectstructuur

```
/
├── frontend/          # Client-side code
├── backend/           # Server-side code
├── shared/            # Gedeelde types en utilities
├── tests/             # Tests
└── .github/
    └── workflows/     # Symphony agent workflows
```

## Testcommando

```bash
npm test
```

<!-- Pas aan: npm test / pnpm test / pytest / etc. -->

---

## Werkwijze coding agent

### Branch

```
feat/GH-{nummer}-{beschrijving}
fix/GH-{nummer}-{beschrijving}
docs/GH-{nummer}-{beschrijving}
test/GH-{nummer}-{beschrijving}
```

### Volgorde van implementatie

1. Backend (routes, services, database)
2. Frontend (components, state, UI)
3. Tests
4. Documentatie indien van toepassing

### Codeerregels

- Alleen bestanden wijzigen die nodig zijn voor dit issue
- Bestaande codestijl en naamgeving volgen
- Geen nieuwe dependencies zonder expliciete reden in het issue
- Geen console.log of debug-code
- Geen refactoring buiten de scope van het issue

### Commitformat

```
{type}(GH-{nummer}): {beschrijving}

- Wat er gedaan is (bullet)
- Nog een bullet indien nodig
- Closes #{nummer}
```

Types: `feat` `fix` `refactor` `docs` `test` `chore`

### PR-beschrijving bevat altijd

- Wat doet deze PR?
- Hoe te testen?
- `Closes #{nummer}`

### Definitie van klaar

- [ ] Functionaliteit werkt zoals beschreven in het issue
- [ ] Alle bestaande tests slagen
- [ ] Nieuwe tests geschreven voor nieuwe logica
- [ ] Geen console.log of debug-code
- [ ] PR geopend en gelinkt aan issue

---

## Review criteria

Deze sectie wordt gebruikt door de review agent om te beoordelen of een PR gemerged mag worden.

### Blokkerende issues (geen auto-merge)

- Falende tests
- Ontbrekende tests voor nieuwe logica
- Functionaliteit die niet overeenkomt met het issue
- Wijzigingen buiten de scope van het issue
- Console.log of debug-code aanwezig
- Nieuwe dependencies zonder reden
- Syntax errors of evidente bugs
- Merge conflicts

### Niet-blokkerende opmerkingen (auto-merge toegestaan)

- Stijlvoorkeur (naamgeving, formatting)
- Suggesties voor betere implementatie
- Ontbrekende documentatie voor kleine wijzigingen
- Kleine optimalisaties

### Auto-merge voorwaarden

Alle van het volgende moet waar zijn:

1. Geen blokkerende issues gevonden door review agent
2. CI-checks slagen (tests groen)
3. Branch heeft geen conflicts met main
4. PR is aangemaakt door Symphony coding agent
