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

### Единый запуск (рекомендуется)

Из **корня проекта** одной командой поднимаются и бэкенд (порт 8000), и фронтенд (Vite, порт 5173). Фронт проксирует `/api` на бэкенд — без запущенного бэкенда будет `ECONNREFUSED` и «Не удалось загрузить данные».

```powershell
# Один раз из корня: установить зависимости для скрипта запуска
npm install

# Запуск backend + frontend (Windows; для Linux/macOS см. ниже)
npm run dev
```

После запуска открывай приложение по адресу: **http://localhost:5173** (логин — по данным из `seed_db`/`seed_user`).

- **Windows:** скрипт использует `backend\venv\Scripts\python.exe`. Убедись, что venv создан: `cd backend && python -m venv venv && pip install -e ".[dev]"`.
- **Linux/macOS:** из корня можно запустить в двух терминалах: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` и `cd frontend && npm run dev`. Либо добавить в корень `package.json` скрипт под свою ОС.

### Backend отдельно

**Запуск backend — всегда из каталога `backend/`.** Конфиг (`backend/app/config.py`) читает переменные из файла `.env` относительно текущей рабочей директории; при CWD = `backend/` подхватывается `backend/.env`. Подробнее: [Environment Policy](docs/architecture/environment-policy.md).

All backend commands run from `backend/`.

```powershell
# Activate venv
backend\venv\Scripts\Activate.ps1

# Install dev dependencies (for linting and testing)
pip install -e ".[dev]"

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

# Lint (run before commit)
ruff check .
ruff format --check .

# Auto-fix lint issues and format
ruff check . --fix
ruff format .
```

Configuration is loaded from `backend/.env` (see `.env.example`). The path to `.env` is resolved relative to the current working directory (CWD), so **run the backend from the `backend/` directory** so that `backend/.env` is used. Tests override `DATABASE_URL` to `sqlite+aiosqlite:///:memory:` in `conftest.py` before importing the app.

## Seed Database (test data)

**Канонический entry point** — скрипт `seed_db.py`. Он создаёт полный набор тестовых данных (2 СТ, владельцы, участки, пользователи, начисления, платежи, расходы, счётчики). Скрипт идемпотентен: повторный запуск не дублирует данные.

- **Обычный сценарий (разработка/демо):**
  ```powershell
  cd backend
  python -m app.scripts.seed_db
  ```
- **Отдельный скрипт `seed_user.py`** — утилитарный: создаёт только пользователя `admin`/`admin`, если его ещё нет. Используй отдельно, когда нужен только один пользователь без полного seed (например, первичная настройка). Для полного набора данных всегда используй `seed_db` (он тоже создаёт пользователей admin, chairman, treasurer).

Модели для скриптов наполнения импортируются только из модулей: `app.modules.<module>.infrastructure.models`. Общего фасада `app.models` нет; ORM-модели существуют только в модулях.

## Testing (backend)

- **Layout:** `tests/test_api/`, `tests/test_models/`, `tests/test_core/`. Fixtures in `tests/conftest.py`: `test_db`, `async_client`, role tokens (e.g. `admin_token`, `treasurer_token`).
- **CI:** Backend tests in GitHub Actions **do not require PostgreSQL**. `conftest.py` sets `DATABASE_URL=sqlite+aiosqlite:///:memory:` before importing the app, so tests run against in-memory SQLite. Do not add a PostgreSQL service or DATABASE_URL to the backend-tests workflow for unit/API tests. If you add an e2e job that needs a real DB, document it in the workflow and in [Environment Policy](docs/architecture/environment-policy.md).
- **Critical:** In `conftest.py`, set `DATABASE_URL` and import `Base` + `register_models` before importing `app.main`; otherwise tests may use the production DB driver.
- **Library docs:** For pytest, FastAPI, httpx patterns use Context7 MCP (see "For AI assistants" below and `.cursor/rules/context7-docs.mdc`). Details and pitfalls: `.cursor/rules/backend-testing-and-pitfalls.mdc`.

## Pitfalls

- Do not import `app` (or anything that loads `app.main`) before setting `DATABASE_URL` and importing models in test setup — the app would attach to the default engine.
- New ORM models must be added in the respective module's `infrastructure/models.py` and imported in `db/register_models.py` so Alembic and test `Base.metadata.create_all` see them.
- **Presentation (API) must not import from Infrastructure.** The type of the current user in `app.api.deps` is the domain entity (`administration.domain.entities.AppUser`); loading from DB is done via the administration module's API layer (e.g. `user_loader.get_user_by_identifier`), which performs ORM→domain mapping inside the module.
- Use `Guid` from `app.db.base` for UUID columns (PostgreSQL + SQLite test compatibility).
- When testing endpoints that use `get_db`, override both `deps.get_db` and `db_session.get_db` in the test client fixture.

### Database connection (Supabase / PostgreSQL)

- **Production/dev:** Use `backend/.env` with `DATABASE_URL=postgresql+asyncpg://...`. The project is set up to work with **Supabase** (or any PostgreSQL). Use the **Connection pool** (Transaction or Session) URI from Supabase → Database settings; prefix with `postgresql+asyncpg://` and URL-encode the password if it contains special characters.
- **Tables:** Created and updated via **Alembic** (`alembic upgrade head`). When implementing features that need new tables or columns, add models, then `alembic revision --autogenerate -m "..."`, then apply with `alembic upgrade head`. The connection is already configured; no extra setup is required to create or test schema changes.
- **Transaction pool (Supabase):** `app/db/session.py` uses `connect_args={"statement_cache_size": 0}` so asyncpg works with pgbouncer (Transaction pool does not support PREPARE).

## Architecture

### Backend Structure (`backend/app/`)

The backend follows Clean Architecture / DDD principles with modular structure:

- `main.py` — FastAPI app factory and middleware setup
- `config.py` — `pydantic-settings` config, reads from `.env`
- `db/base.py` — `DeclarativeBase` and custom `Guid` type (UUID on PostgreSQL, CHAR(36) on SQLite for test compatibility)
- `db/session.py` — async engine, session maker, `get_db()` dependency
- `db/register_models.py` — imports all models from modules for Alembic
- `modules/` — modular Clean Architecture structure (see below)
- `api/deps.py` — shared FastAPI dependencies
- `core/security.py` — shared utilities (JWT, bcrypt)

### Module Structure (`backend/app/modules/`)

Each module follows the same Clean Architecture pattern:

```
{module_name}/
├── domain/           # Pure Python (entities, repositories, events)
│   ├── entities.py   # Business objects (no framework dependencies)
│   ├── repositories.py # Repository interfaces (ABC)
│   └── events.py     # Domain events
├── application/      # Use cases and DTOs
│   ├── use_cases.py  # Business operations
│   └── dtos.py       # Data transfer objects (Pydantic)
├── infrastructure/   # Framework-specific implementations
│   ├── models.py     # SQLAlchemy ORM models
│   └── repositories.py # Repository implementations
└── api/              # FastAPI layer
    ├── routes.py     # API endpoints
    └── schemas.py    # API request/response schemas
```

**Modules:**
- `cooperative_core` — Cooperative management
- `land_management` — Land plots, owners, ownerships
- `financial_core` — Financial subjects, balances
- `accruals` — Contributions and accruals
- `payments` — Payment processing
- `expenses` — Expense tracking
- `meters` — Meters and readings
- `reporting` — Reports and analytics
- `administration` — Authentication and user management

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
- `docs/architecture/` — ADRs (`adr/` — индекс и процесс см. [adr/README.md](docs/architecture/adr/README.md)), glossary per domain (`glossary/`), common definitions (`common/`)
- `docs/processes/` — BPMN 2.0 business process files, interactive viewer (`bpmn-viewer.html`)
- `domains/{domain_name}/` — domain-specific L2 diagrams (e.g. `domains/bank_statements/container-diagram.mmd`)

### Schema First Principle

Architecture diagrams and data model diagrams **must be updated before** any code changes. Do not implement features or integrations not reflected in diagrams.

## Project Conventions

- **Diagrams:** Mermaid only. No PlantUML. C4 Model for architecture (L1 System Context, L2 Container priority). BPMN 2.0 for business processes (stored as `.bpmn` in `docs/processes/{domain}/`).
- **C4 naming:** `Person_`, `Service_`, `System_`, `Database_` prefixes (e.g. `Person_Sobstvennik`, `Service_ContributionManager`, `Database_PostgreSQL_ST`)
- **Soft deletion** for financial entities (`status = archived|cancelled`); hard delete is forbidden for Accrual, Payment, Expense.
- **ADR required** for every significant architectural decision. Index and process: [docs/architecture/adr/README.md](docs/architecture/adr/README.md). Format: Context / Decision / Consequences.
- **Glossary** required per domain (`docs/architecture/glossary/{domain}.md`). **Only Lead Architect** may create or modify glossary files; no other role or agent may edit them. Rationale: single source of truth for ubiquitous language; see [docs/architecture/glossary/README.md](docs/architecture/glossary/README.md). Full restricted paths: [docs/architecture/OWNERSHIP.md](docs/architecture/OWNERSHIP.md).
- **Don't invent business requirements.** When sources, formulas, or processes are unclear — stop, ask explicit questions, list missing information.
- **Folder structure is DDD-based** — organized by business domain, not technical layer.

### For AI assistants (Cursor, etc.)

- **Code citations:** When referencing code from the repo, use the format `startLine:endLine:path/to/file` (e.g. `12:15:backend/app/main.py`). No other citation format.
- **Parallel tool use:** Run independent operations (searches, file reads, grep) in parallel when possible instead of sequentially.
- **Language:** Respond in Russian unless the user asks otherwise (see Project Conventions).
- **Rules:** Project-specific rules live in `.cursor/rules/` (code style, architecture, workflow); follow them when applicable.
- **Context7 (use always for library docs):** For any library/API documentation or code examples (FastAPI, SQLAlchemy, Vue, Pydantic, pytest, Alembic, httpx, etc.) **always** use Context7 MCP — do not rely on model knowledge alone. Config: `.cursor/mcp.json`; rule: `.cursor/rules/context7-docs.mdc`. [Context7](https://github.com/upstash/context7). API key (optional): [context7.com/dashboard](https://context7.com/dashboard) → set in `.cursor/mcp.json` locally; do not commit keys.
