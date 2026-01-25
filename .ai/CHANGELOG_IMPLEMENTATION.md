# Implementation Changelog (v2: physical persons, SNT members, plots)

All changes under `PLAN_V2_IMPLEMENTATION.md` are recorded here. Format: date (UTC), description, files.

---

## 2026-01-24

- **Plan and log:** created `PLAN_V2_IMPLEMENTATION.md` and `CHANGELOG_IMPLEMENTATION.md`.

- **Backend v2:** added `backend_snt_v2/`.
  - `requirements.txt`, `alembic.ini`, `alembic/env.py`, `script.py.mako`, `README`, `alembic/versions/0001_init_v2.py`
  - `app/config.py`, `app/db/base.py`, `app/db/session.py`
  - Models: `physical_person`, `snt`, `snt_member`, `plot`, `plot_owner`
  - Schemas: `app/schemas/v2.py`
  - API: `app/api/router.py` — `GET /api/snts`, `/physical-persons`, `/physical-persons/{id}`, `/snt-members?snt_id=`, `/plots?snt_id=`
  - `app/main.py` (FastAPI + CORS), `scripts/seed.py`, `scripts/init_db.py`, `run.ps1`
  - SQLite `snt_v2.db`, seed: 3 SNTs, 8 physical persons, memberships, plots, plot_owners (one person in two SNTs and two plots).

- **Frontend v2:** updated `frontend/index.html`, `app.js`, `styles.css`.
  - Nav: Overview, SNT, Physical persons, SNT members, Plots. Data from `http://localhost:8001/api`.
  - SNT selector in header; on change, reload members and plots.
  - Overview: cards (physical persons, SNTs, members, plots for selected SNT).
  - Physical persons: table; row click → modal (phone, INN, memberships, plots).
  - SNT members / Plots: tables, filter by selected SNT.
  - Minimal UI (DM Sans, neutral palette, simple icons), theme toggle kept.
  - Added `run-v2.ps1`, `backend_snt_v2/README.md`.

---

## 2026-01-24 (meters, users, isolation)

- **Meters:** model `meter.py` (`snt_id`, `plot_id`, `meter_type` electricity/water, `serial_number`). Uniqueness `(snt_id, plot_id, meter_type)`. Migration `0002_meter_app_user`. Seed: two meters per plot (water + electricity). API `GET /api/meters?snt_id=`.

- **Users and roles (no‑password auth):** model `app_user` (`name`, `role` admin|snt_user, `snt_id` for snt_user). Seed: “Administrator” (admin); one user per SNT name (snt_user). API `GET /api/users`, `GET /api/me` (from `X-User-Id`). All protected calls use `X-User-Id`.

- **Strict isolation for snt_user:** Admin sees all SNTs and data. SNT user: SNT selector hidden, access only to own SNT. `get_current_user` from `X-User-Id`; endpoints filter by `user.snt_id` for snt_user.

- **Frontend:** User selector in header; choice in `localStorage`. For SNT user, SNT selector hidden. “Meters” section: table (plot, SNT, type, serial). All API calls (except `/users`) send `X-User-Id`.

- **Files:** `meter.py`, `app_user.py`, `0002_meter_app_user.py`, `deps.py`, `router.py`, `v2.py`, `seed.py`, frontend files.
