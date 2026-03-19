# AGENTS.md

AI assistants: read this file first. Respond in Russian unless told otherwise.

## Project Overview

**Controlling** — accounting system for garden cooperatives (СТ) in Belarus. Handles contributions, payments, debt tracking, land plots, meters, and reporting. All amounts in **BYN** only.

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 15+
- **Frontend:** Vue 3 + TypeScript + Vite + Pinia
- **Auth:** JWT + bcrypt | **Tests:** pytest (backend), Vitest (frontend) | **Lint:** ruff

## Key References

| What | Where |
|------|-------|
| Development plan, top-5 tasks, roadmap | `docs/development-index.md` |
| Current session focus | `docs/plan/current-focus.md` |
| Architecture, ADR, glossaries | `docs/architecture/` |
| Data model | `docs/data-model/schema-viewer.html` |
| Agent roles | `.cursor/rules/agents/` |
| Build & run instructions | `docs/development-index.md` §4.8 |

## Architecture (brief)

Backend: Clean Architecture / DDD. Modules in `backend/app/modules/`: `cooperative_core`, `land_management`, `financial_core`, `accruals`, `payments`, `expenses`, `meters`, `reporting`, `administration`. Each module: `domain/` → `application/` → `infrastructure/` → `api/`.

## Owner Communication

The project owner is not a developer. Use simple language, no jargon, no code blocks for them. Ask questions one at a time. Details: `.cursor/rules/communication-style.mdc`.

## Critical Pitfalls

- Run backend from `backend/` dir (`.env` is CWD-relative).
- New ORM models → import in `db/register_models.py`.
- API layer must NOT import from Infrastructure.
- Use `Guid` from `app.db.base` for UUID columns.
- Tests: set `DATABASE_URL` before importing `app.main`.
- Library docs: use Context7 MCP, not model knowledge.
