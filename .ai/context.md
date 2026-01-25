# Project context

## Short project goal

Accounting system for **SNT** (садовые некоммерческие товарищества — gardening associations). Manages partnerships (СНТ), plots, owners/members, meters, and—in the full vision—accruals and payments. **v2** focuses on separated **physical persons** and **SNT members**, plot ownership, meters, and strict per‑SNT data isolation for non‑admin users.

---

## Main constraints

- **Frontend is not the source of truth.** All invariants and calculations live in backend/DB.
- **Multi‑tenant by SNT.** All relevant tables have `snt_id`; data of different SNTs must not mix.
- **Strict isolation for `snt_user`.** Users bound to a single SNT must never see another SNT's data.
- **Auth without passwords.** Only user selection in UI; identity via `X-User-Id` header. No sessions/tokens.
- **v1 backend (`backend_snt_core`) is left unchanged.** v2 lives in `backend_snt_v2`; no shared code.

---

## Technology stack

| Layer | v1 (core) | v2 (current UI backend) | Frontend |
|-------|-----------|--------------------------|----------|
| Runtime | Python | Python | Browser |
| Framework | FastAPI | FastAPI | Vanilla JS |
| DB | PostgreSQL | SQLite | — |
| ORM | SQLAlchemy | SQLAlchemy | — |
| Migrations | Alembic | Alembic | — |
| Config | pydantic-settings | pydantic-settings | — |
| UI | — | — | HTML, CSS, `fetch` |

- **Ports:** v1 API :8000, v2 API :8001, frontend static server :3000.
- **Scripts:** `run.ps1` per backend, `run-v2.ps1` runs v2 + frontend (PowerShell, Windows).
