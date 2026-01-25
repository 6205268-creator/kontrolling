# Architecture

## System components

| Component | Path | Purpose |
|-----------|------|---------|
| **Backend v1 (core)** | `backend_snt_core/` | Full accounting: documents, posting, `reg_balance`. PostgreSQL. API :8000. |
| **Backend v2** | `backend_snt_v2/` | Refbooks + links (physical persons, members, plots, meters, users). SQLite. API :8001. |
| **Frontend** | `frontend/` | SPA-like UI: user/SNT selectors, dashboards, tables, modals. Reads from v2 API only. |
| **Static server** | `frontend/run.ps1` | Serves `frontend/` on :3000 (e.g. `python -m http.server`). |

**Supporting:**
- `run-v2.ps1` — init DB (migrations + seed), start v2 API, start frontend server, open browser.
- `PLAN_V2_IMPLEMENTATION.md`, `CHANGELOG_IMPLEMENTATION.md` — plan and change log.

---

## Interactions

```
┌─────────────┐     GET /api/*      ┌──────────────────┐     SQL     ┌─────────────┐
│  Frontend   │ ──────────────────► │  Backend v2      │ ◄──────────► │  SQLite     │
│  :3000      │     X-User-Id       │  FastAPI :8001   │             │  snt_v2.db  │
└─────────────┘                     └──────────────────┘             └─────────────┘
```

- Frontend calls only **v2** API (`http://localhost:8001/api`). No direct use of v1.
- **v1** is standalone: Swagger/main page, own DB, run via `backend_snt_core/run.ps1`.
- All v2 endpoints (except `GET /users`) use `get_current_user` from `X-User-Id` and apply SNT filtering for `snt_user`.

---

## Data flow

1. **Page load:** Frontend fetches `/users`, then selects user (or uses `localStorage`). Sends `X-User-Id` on subsequent requests.
2. **User switch:** Frontend calls `/me`, then `/snts`. If admin → SNT selector shown; if `snt_user` → selector hidden, single SNT fixed.
3. **Section views:** Frontend requests `/physical-persons`, `/snt-members?snt_id=`, `/plots?snt_id=`, `/meters?snt_id=` as needed. For `snt_user`, backend ignores `snt_id` and uses `user.snt_id`.
4. **Physical person detail:** Click row → `GET /physical-persons/{id}` → modal with memberships and plot ownerships. For `snt_user`, 404 if person has no link to their SNT.

**v1 (core) flow:** CRUD via REST → services → DB. Posting/unposting updates `reg_balance`; UI (main page) talks to v1 API only when used.

---

## External integrations

- **None.** No third‑party APIs, message queues, or external services.
- Frontend uses Google Fonts (DM Sans) via `<link>`; no server-side integration.
