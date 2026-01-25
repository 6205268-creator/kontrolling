# SNT Accounting Development Log

All material project changes are recorded here: folders/files created, dependencies, commands run.

---

## 2026-01-20

- Created `DEV_LOG.md` for development history.
- Decision: use `FastAPI + SQLAlchemy + PostgreSQL` for the new SNT core accounting backend.
- Existing Node.js backend and frontend unchanged; separate Python backend for core.

### SNT Core Backend

- Created `backend_snt_core` for Python backend.
- Added `backend_snt_core/README.md`, `backend_snt_core/requirements.txt` (fastapi, uvicorn, SQLAlchemy, psycopg, alembic, pydantic, pydantic-settings).
- FastAPI app: `app/main.py` (`GET /health`), `app/config.py` (DATABASE_URL from `.env`), `app/db/base.py`, `app/db/session.py`.
- Created `ARCHITECTURE_SNT_CORE.md` (data model, documents, registers, posting/unposting).
- Python venv: `python -m venv .venv`; installed dependencies (fastapi, SQLAlchemy, alembic, etc.).

### Cleanup (Telegram/Frontend)

- Removed old `frontend/`, `backend/` (Node.js / Telegram).
- Updated root `README.md`: removed Telegram instructions, described core and FastAPI run.

### Migrations and schema

- Initialized Alembic: `.venv\Scripts\alembic -c backend_snt_core\alembic.ini init backend_snt_core\alembic`.
- Configured `alembic/env.py`: `Base.metadata`, `DATABASE_URL` from env.
- Migration `0001_init_schema.py`: tables `snt`, `plot`, `owner`, `plot_owner`, `charge_item`, `doc_accrual`, `doc_accrual_row`, `doc_payment`, `doc_payment_row`, `reg_balance` + FK/CHECK/indexes.
- SQLAlchemy models in `backend_snt_core/app/models/`.

### REST API and posting

- Routes: `POST/GET /snts`, `/snts/{snt_id}/plots`, `/owners`, `/charge-items`, `/documents/accruals`, `/documents/payments` (+ post/unpost), `GET /snts/{snt_id}/reports/balance?on_date=`.
- Posting services: `services/posting/accrual.py`, `payment.py`.

### Seed

- `backend_snt_core/scripts/seed.py`: 3 SNTs, 10–15 owners and plots each; charge items; accrual/payment docs, posted (register movements).

### Run and test

- `backend_snt_core/run.ps1`: migrations + seed + API. FastAPI on :8000, Swagger at `http://127.0.0.1:8000/docs`.

**Before run:** PostgreSQL up, `DATABASE_URL` set; run migrations and seed (see `DEV_LOG_ru.md` or `backend_snt_core/README.md` for exact commands).
