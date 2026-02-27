# AGENTS.md

This file provides guidance to AI assistants (WARP, Cursor, etc.) when working with code in this repository.

## Project Overview

**Controlling** — accounting system for garden cooperatives (Садоводческие Товарищества, СТ) in Belarus. Handles contributions, payments, debt tracking, land plots, meters, and reporting. All monetary amounts are in **BYN** (Belarusian rubles) only; no multi-currency support.

**Language convention:** respond in Russian unless told otherwise.

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 15+ (asyncpg)
- **Frontend:** Vue 3 + TypeScript + Vite + Pinia (not yet scaffolded — `frontend/` is empty)
- **Auth:** JWT + bcrypt (python-jose, passlib)
- **Tests:** pytest + pytest-asyncio (backend), Vitest (frontend, planned)
- **Linting:** ruff (line-length 100, target py311)

## Build & Development Commands

All backend commands run from `backend/`.

```powershell
# Activate venv
backend\venv\Scripts\Activate.ps1

# Run dev server
uvicorn app.main:app --reload

# Run all tests (uses in-memory SQLite — no PostgreSQL required)
pytest

# Run a single test file / single test
pytest tests/test_health.py
pytest tests/test_health.py::test_health_returns_ok

# Alembic migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Lint
ruff check .
ruff format .
```

Configuration is loaded from `backend/.env` (see `.env.example`). Tests override `DATABASE_URL` to `sqlite+aiosqlite:///:memory:` in `conftest.py` before importing the app.

## Testing (backend)

- **Layout:** `tests/test_api/`, `tests/test_services/`, `tests/test_schemas/`, `tests/test_models/`, `tests/test_core/`. Fixtures in `tests/conftest.py`: `test_db`, `async_client`, role tokens (e.g. `admin_token`, `treasurer_token`).
- **Critical:** In `conftest.py`, set `DATABASE_URL` and import `Base` + `app.models` before importing `app.main`; otherwise tests may use the production DB driver.
- **Library docs:** For pytest, FastAPI, httpx patterns use Context7 MCP (see "For AI assistants" below and `.cursor/rules/context7-docs.mdc`). Details and pitfalls: `.cursor/rules/backend-testing-and-pitfalls.mdc`.

## Pitfalls

- Do not import `app` (or anything that loads `app.main`) before setting `DATABASE_URL` and importing models in test setup — the app would attach to the default engine.
- New ORM models must be imported and listed in `app/models/__init__.py` so Alembic and test `Base.metadata.create_all` see them.
- Use `Guid` from `app.db.base` for UUID columns (PostgreSQL + SQLite test compatibility).
- When testing endpoints that use `get_db`, override both `deps.get_db` and `db_session.get_db` in the test client fixture.

### Database connection (Supabase / PostgreSQL)

- **Production/dev:** Use `backend/.env` with `DATABASE_URL=postgresql+asyncpg://...`. The project is set up to work with **Supabase** (or any PostgreSQL). Use the **Connection pool** (Transaction or Session) URI from Supabase → Database settings; prefix with `postgresql+asyncpg://` and URL-encode the password if it contains special characters.
- **Tables:** Created and updated via **Alembic** (`alembic upgrade head`). When implementing features that need new tables or columns, add models, then `alembic revision --autogenerate -m "..."`, then apply with `alembic upgrade head`. The connection is already configured; no extra setup is required to create or test schema changes.
- **Transaction pool (Supabase):** `app/db/session.py` uses `connect_args={"statement_cache_size": 0}` so asyncpg works with pgbouncer (Transaction pool does not support PREPARE).

## Architecture

### Backend Structure (`backend/app/`)

- `main.py` — FastAPI app factory and middleware setup
- `config.py` — `pydantic-settings` config, reads from `.env`
- `db/base.py` — `DeclarativeBase` and custom `Guid` type (UUID on PostgreSQL, CHAR(36) on SQLite for test compatibility)
- `db/session.py` — async engine, session maker, `get_db()` dependency
- `models/` — SQLAlchemy ORM models (all re-exported in `__init__.py` so Alembic sees them)
- `schemas/` — Pydantic schemas (request/response DTOs)
- `api/` — route handlers; `deps.py` for shared FastAPI dependencies
- `services/` — domain business logic (land_plot_service, owner_service, balance_service, etc.)
- `core/` — shared utilities (e.g. security, auth helpers)

### Key Domain Concepts

- **Cooperative** — a garden cooperative (СТ); the tenant boundary
- **LandPlot** — a plot of land within a cooperative
- **Owner** — a person or legal entity; linked to plots only via **PlotOwnership** (no direct LandPlot→Owner FK)
- **PlotOwnership** — temporal ownership record with fractional shares (`share_numerator/share_denominator`), `is_primary` = member of СТ
- **FinancialSubject** — the central financial abstraction; all `Accrual` and `Payment` records must go through a FinancialSubject, never directly to a plot or meter
- **Multi-tenancy** is data-level: `cooperative_id` on LandPlot, FinancialSubject, Expense; Owner has no direct cooperative FK

### Role-specific guidance (`docs/agents/`)

Role prompts for backend, frontend, QA, DevOps, security, UX/UI, project orchestration, SEO. Use when you need to follow a specific role’s checklist or style (e.g. “work as backend-developer” → see [docs/agents/backend-developer.md](docs/agents/backend-developer.md)). Index: [docs/agents/README.md](docs/agents/README.md).

### Documentation & Diagrams (`docs/`)

- `docs/project-design.md` — full system design (data model, roles, domain events)
- `docs/project-implementation.md` — feature implementation roadmap
- `docs/data-model/` — conceptual model, entity specs, interactive schema viewer (`schema-viewer.html`)
- `docs/architecture/` — C4 diagrams, ADRs (`adr/`), glossary per domain (`glossary/`), common definitions (`common/`)
- `docs/processes/` — BPMN 2.0 business process files, interactive viewer (`bpmn-viewer.html`)
- `domains/{domain_name}/` — domain-specific L2 diagrams (e.g. `domains/bank_statements/container-diagram.mmd`)

### Schema First Principle

Architecture diagrams and data model diagrams **must be updated before** any code changes. Do not implement features or integrations not reflected in diagrams.

## Project Conventions

- **Diagrams:** Mermaid only. No PlantUML. C4 Model for architecture (L1 System Context, L2 Container priority). BPMN 2.0 for business processes (stored as `.bpmn` in `docs/processes/{domain}/`).
- **C4 naming:** `Person_`, `Service_`, `System_`, `Database_` prefixes (e.g. `Person_Sobstvennik`, `Service_ContributionManager`, `Database_PostgreSQL_ST`)
- **Soft deletion** for financial entities (`status = archived|cancelled`); hard delete is forbidden for Accrual, Payment, Expense.
- **ADR required** for every significant architectural decision (`docs/architecture/adr/`).
- **Glossary** required per domain (`docs/architecture/glossary/{domain}.md`).
- **Don't invent business requirements.** When sources, formulas, or processes are unclear — stop, ask explicit questions, list missing information.
- **Folder structure is DDD-based** — organized by business domain, not technical layer.

### For AI assistants (Cursor, etc.)

- **Code citations:** When referencing code from the repo, use the format `startLine:endLine:path/to/file` (e.g. `12:15:backend/app/main.py`). No other citation format.
- **Parallel tool use:** Run independent operations (searches, file reads, grep) in parallel when possible instead of sequentially.
- **Language:** Respond in Russian unless the user asks otherwise (see Project Conventions).
- **Rules:** Project-specific rules live in `.cursor/rules/` (code style, architecture, workflow); follow them when applicable.
- **Context7 (use always for library docs):** For any library/API documentation or code examples (FastAPI, SQLAlchemy, Vue, Pydantic, pytest, Alembic, httpx, etc.) **always** use Context7 MCP — do not rely on model knowledge alone. Config: `.cursor/mcp.json`; rule: `.cursor/rules/context7-docs.mdc`. [Context7](https://github.com/upstash/context7). API key (optional): [context7.com/dashboard](https://context7.com/dashboard) → set in `.cursor/mcp.json` locally; do not commit keys.
