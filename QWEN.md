# КОНТРОЛЛИНГ — Project Context

**Accounting system for garden cooperatives (Садоводческие Товарищества, СТ) in Belarus.**

Handles contributions, payments, debt tracking, land plots, meters, and reporting. All monetary amounts are in **BYN** (Belarusian rubles).

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+ • FastAPI • SQLAlchemy 2.0 (async) • Alembic • PostgreSQL 15+ (asyncpg) |
| **Frontend** | Vue 3 + TypeScript • Vite • Pinia • Vue Router |
| **Auth** | JWT + bcrypt (python-jose, passlib) |
| **Tests** | pytest + pytest-asyncio (backend) • Vitest (frontend) • Playwright (e2e) |
| **Linting** | ruff (line-length 100, target py311) |

---

## Project Structure

```
kontrolling/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app factory
│   │   ├── config.py           # pydantic-settings config
│   │   ├── db/                 # DB session, base model
│   │   ├── api/deps.py         # Shared dependencies
│   │   └── modules/            # Clean Architecture modules (9 domains)
│   ├── tests/                  # Backend tests (197 tests)
│   ├── alembic/                # DB migrations
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                   # Vue 3 SPA (15 views, 6 Pinia stores)
│   ├── src/
│   ├── e2e/                    # Playwright e2e tests
│   └── package.json
├── docs/                       # Comprehensive documentation
│   ├── development-index.md    # Single entry point (START HERE)
│   ├── project-design.md       # System architecture
│   ├── project-implementation.md # Feature roadmap (35/35 complete)
│   ├── data-model/             # ER diagrams, schema viewer
│   ├── architecture/           # ADRs, glossaries, environment policy
│   ├── plan/                   # Current focus, workflow docs
│   ├── tasks/                  # Task files, specs, checklists
│   └── history/                # PENDING_GAPS, RESOLVED_GAPS
├── .cursor/rules/              # Cursor agent rules
│   ├── agents/                 # Role-specific rules
│   ├── git-branch-policy.mdc   # Branch workflow rule
│   └── architecture-guardian.mdc # Architecture review rule
├── docker-compose.yml          # Full stack deployment
├── package.json                # Root dev scripts (npm run dev)
└── QWEN.md                     # This file
```

---

## Building & Running

### Unified Dev Launch (Recommended)

From **project root**, starts both backend (port 8000) and frontend (port 5173):

```powershell
# One-time setup
npm install

# Run both services (Windows)
npm run dev
```

Access: **http://localhost:5173** (frontend proxies `/api` to backend).

### Backend Only

**Always run backend from `backend/` directory** — config reads `.env` relative to CWD.

```powershell
# Create/activate venv (one-time)
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload

# Run tests (uses in-memory SQLite — no PostgreSQL needed)
pytest
pytest tests/test_health.py::test_health_returns_ok

# Alembic migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Lint
ruff check .
ruff format --check .
```

### Frontend Only

```powershell
cd frontend
npm install
npm run dev
```

### Docker Deployment

```bash
docker compose up --build -d
```

Runs **db** and **backend** only. Start frontend separately: from project root `npm run dev`, then open http://localhost:5173.

Access:
- **Frontend:** http://localhost:5173 (after `npm run dev`)
- **Backend API:** http://localhost:8000
- **Swagger docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/api/health

---

## Seed Database (Test Data)

**Canonical entry point** — `seed_db.py` creates full test dataset (2 cooperatives, owners, plots, users, accruals, payments, expenses, meters). Idempotent.

```powershell
cd backend
python -m app.scripts.seed_db
```

---

## Architecture

### Clean Architecture Module Pattern

Each module in `backend/app/modules/` follows:

```
{module_name}/
├── domain/           # Pure Python (entities, repositories, events)
│   ├── entities.py
│   ├── repositories.py
│   └── events.py
├── application/      # Use cases and DTOs
│   ├── use_cases.py
│   └── dtos.py
├── infrastructure/   # Framework-specific implementations
│   ├── models.py     # SQLAlchemy ORM models
│   └── repositories.py
└── api/              # FastAPI layer
    ├── routes.py
    └── schemas.py
```

### Modules

| Module | Purpose |
|--------|---------|
| `cooperative_core` | Cooperative management |
| `land_management` | Land plots, owners, ownerships |
| `financial_core` | Financial subjects, balances |
| `accruals` | Contributions and accruals |
| `payments` | Payment processing |
| `expenses` | Expense tracking |
| `meters` | Meters and readings |
| `reporting` | Reports and analytics |
| `administration` | Authentication and user management |

### Key Domain Concepts

- **Cooperative** — garden cooperative (СТ); tenant boundary
- **LandPlot** — plot of land within a cooperative
- **Owner** — person/legal entity; linked to plots via **PlotOwnership** (no direct FK)
- **PlotOwnership** — temporal ownership with fractional shares (`share_numerator/share_denominator`), `is_primary` = СТ member
- **FinancialSubject** — central financial abstraction; all `Accrual` and `Payment` go through it (never directly to plot/meter)
- **Multi-tenancy** — data-level via `cooperative_id` on LandPlot, FinancialSubject, Expense

---

## Development Conventions

### Code Style

- **Line length:** 100 characters
- **Python target:** 3.11
- **Diagrams:** Mermaid only (no PlantUML)
- **C4 naming:** `Person_`, `Service_`, `System_`, `Database_` prefixes

### Testing

- **Backend:** `pytest` from `backend/` (uses in-memory SQLite)
- **Fixtures:** `test_db`, `async_client`, role tokens in `tests/conftest.py`
- **Critical:** Set `DATABASE_URL` and import models **before** importing `app.main` in tests

### Architecture Rules

- **Schema First:** Update diagrams **before** code changes
- **Soft deletion:** Financial entities use `status = archived|cancelled`; hard delete forbidden
- **ADR required:** Every significant architectural decision needs an ADR
- **Glossary ownership:** Only Lead Architect may edit glossary files
- **Don't invent business requirements:** Ask when unclear

### Pre-Commit Checklist

Before committing, verify:

- [ ] `pytest` — all tests green
- [ ] `ruff check .` — no errors
- [ ] `ruff format --check .` — formatting OK
- [ ] `python -m app.scripts.architecture_linter` — all checks passed (exit code 0)
- [ ] `python -m app.scripts.seed_db` — seed data created without errors
- [ ] Diagrams updated (if data model changed)
- [ ] Restricted paths not touched (or approved by Lead Architect)

---

## Agent Workflow (Isolated Tasks)

For any isolated task (features, refactoring, bug fixes):

### 1. Branch Policy

- **Never commit to `main` or `master`**
- Work only in the specified feature branch
- Merge to main only after explicit user approval
- If branch doesn't exist → ask user before creating
- If branch exists → check status, show last 5 commits, ask for confirmation

**Rule file:** `.cursor/rules/git-branch-policy.mdc`

### 2. Stage Execution

For each stage of a multi-stage task:

1. Agent outputs stage plan, waits for "yes"/"start"
2. Makes changes in working branch
3. Runs checks in order:
   - `pytest` (all tests green)
   - `ruff check .` + `ruff format --check .` (no errors)
   - `python -m app.scripts.architecture_linter` (exit code 0)
   - `python -m app.scripts.seed_db` (no errors)
4. Calls `@architecture-guardian` for review
5. Fixes issues (minor → immediately, major → after user confirmation)
6. Proceeds to next stage only after all checks pass

**Workflow doc:** `docs/plan/agent-isolated-task-workflow.md`

### 3. Architecture Guardian Review

After each stage, call `@architecture-guardian` to check:

1. **Layer boundaries** — API doesn't import from infrastructure
2. **Financial core** — Accrual/Payment use FinancialSubject
3. **Data model** — models registered in `register_models.py`
4. **Tests** — all tests pass, new logic covered
5. **Diagrams** — updated if model changed

**Rule file:** `.cursor/rules/agents/architecture-guardian.mdc`

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [`docs/development-index.md`](docs/development-index.md) | **START HERE** — Single entry point, Top-5 tasks, roadmap |
| [`docs/project-design.md`](docs/project-design.md) | Full system design |
| [`docs/project-implementation.md`](docs/project-implementation.md) | Feature roadmap (35/35 complete) |
| [`docs/data-model/schema-viewer.html`](docs/data-model/schema-viewer.html) | Interactive schema viewer |
| [`docs/architecture/environment-policy.md`](docs/architecture/environment-policy.md) | Environment variables policy |
| [`docs/architecture/adr/README.md`](docs/architecture/adr/README.md) | ADR process |
| [`docs/plan/current-focus.md`](docs/plan/current-focus.md) | Current task focus, what to do next |
| [`docs/plan/agent-isolated-task-workflow.md`](docs/plan/agent-isolated-task-workflow.md) | Universal workflow for isolated tasks |
| [`docs/tasks/workflow-orchestration.md`](docs/tasks/workflow-orchestration.md) | Workflow orchestration, pre-commit checklist |

---

## For AI Assistants

### Context7 MCP (Use Always)

For **any library/API documentation** (FastAPI, SQLAlchemy, Vue, Pydantic, pytest, Alembic, httpx, etc.) **always** use Context7 MCP — don't rely on model knowledge.

Config: `.cursor/mcp.json` | Rule: `.cursor/rules/context7-docs.mdc`

### Code Citations

Use format: `startLine:endLine:path/to/file` (e.g., `12:15:backend/app/main.py`)

### Language

Respond in **Russian** unless user requests otherwise.

### Rules

Project-specific rules in `.cursor/rules/` — follow when applicable:

| Rule | Purpose |
|------|---------|
| `.cursor/rules/git-branch-policy.mdc` | Branch workflow for isolated tasks |
| `.cursor/rules/architecture-guardian.mdc` | Architecture review checklist |
| `.cursor/rules/development-index-rule.mdc` | Always read development index first |
| `.cursor/rules/project-conventions.mdc` | SOLID, KISS, no invented requirements |
| `.cursor/rules/agents/` | 10 role-specific prompts (backend, frontend, QA, DevOps, etc.) |

---

## Quick Reference

```powershell
# Full dev environment (Windows)
npm install                          # Root dependencies
cd backend && python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd ..
npm run dev                          # Start both services

# Database seed
cd backend && python -m app.scripts.seed_db

# Run tests
cd backend && pytest

# Architecture linter
cd backend && python -m app.scripts.architecture_linter

# Docker deploy
docker compose up --build -d
```

---

## Project Status

- **Backend:** ✅ 35/35 features complete (100%)
- **Tests:** ✅ 197 tests passing
- **Frontend:** ✅ 15 views, 6 Pinia stores, Playwright e2e
- **Docker:** ✅ Full stack deployment ready
- **Documentation:** ✅ Comprehensive (development index, ADRs, glossaries)
- **Agent Workflow:** ✅ Branch policy + architecture guardian implemented

**Next priorities:**
1. Glossary completion (7/10 domains pending — Low priority)
2. Frontend Clean Architecture migration (post-MVP)
3. E2E test coverage expansion
4. OpenAPI documentation (post-MVP)
5. Docker e2e verification

---

## Current Task Focus

**Ledger-ready MVP** — Temporary financial model, operation irreversibility, balance on date, preparation for ledger transition.

- **Branch:** `feature/ledger-ready-mvp`
- **Status:** Specification ready, implementation not started
- **Stages:** 5 (model → balance rule → cancellation → amount protection → domain events)
- **Spec:** `docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`
- **Focus:** `docs/plan/current-focus.md`
