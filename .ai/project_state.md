# Project state

## Current progress

- **v1 (backend_snt_core):** Implemented and stable. PostgreSQL, documents, posting, `reg_balance`, REST API, seed. No UI except Swagger / simple main page.
- **v2 (backend_snt_v2):** Implemented. SQLite, refbooks (physical persons, SNTs, members, plots, meters, users), REST API, auth via `X-User-Id`, strict SNT isolation for `snt_user`.
- **Frontend:** Implemented. Consumes v2 API only. User + SNT selectors, dashboard, physical persons / members / plots / meters tables, physical-person detail modal. View‑only.

---

## Implemented parts

| Area | Details |
|------|---------|
| **v2 API** | `GET /users`, `/me`, `/snts`, `/physical-persons`, `/physical-persons/{id}`, `/snt-members`, `/plots`, `/meters`. All filtered by `X-User-Id` and role. |
| **v2 DB** | Models + migrations `0001_init_v2`, `0002_meter_app_user`. Seed: 3 SNTs, 8 physical persons, members, plots, plot_owners, users (1 admin + 3 snt_user), meters (water + electricity per plot). |
| **Auth** | `get_current_user` from `X-User-Id`. Default to first admin if missing/invalid. No passwords. |
| **Isolation** | `snt_user` restricted to `user.snt_id` in all relevant endpoints. Frontend hides SNT selector for `snt_user`. |
| **Frontend** | Sections: Обзор, СНТ, Физ. лица, Члены СНТ, Участки, Счётчики. Theme toggle, `localStorage` for user. |

---

## Pending tasks

- **Documents and posting in v2:** No `doc_accrual`, `doc_payment`, or `reg_balance` in v2. Accruals, payments, and register logic exist only in v1.
- **`charge_item` in v2:** Refbook of charge types not added to v2.
- **CRUD in frontend:** No create/edit/delete for persons, plots, meters, etc.; read‑only.
- **Meters in physical-person modal:** Detail view shows memberships and plot ownerships only; meters per plot are not shown there.
- **Configurable API base:** Frontend uses hardcoded `http://localhost:8001`.

---

## Known issues

- **`X-User-Id` is trusted:** No crypto or signing; header can be forged to impersonate a user.
- **`run-v2.ps1`:** Assumes Windows/PowerShell and `python` on PATH (or venv); may need adjustment on other setups.
- **v1:** Requires PostgreSQL plus migrations and seed (see `DEV_LOG.md`); not used by current frontend.
