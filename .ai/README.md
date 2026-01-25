# kontrolling — SNT accounting

1C‑like recalculation‑based accounting for SNT (gardening associations):

- **PostgreSQL** (v1) — documents, posting, `reg_balance`.
- **SQLite** (v2) — refbooks: physical persons, SNT members, plots, meters, users. API :8001.
- **Frontend** (Vanilla JS) — dashboard, tables, modals. Port :3000.
- UI/frontend is not the source of truth; all invariants live in backend/DB.

Architecture: `.ai/architecture.md`, `.ai/context.md`.

## Quick start

### v2 + frontend (recommended)

```powershell
.\run-v2.ps1
```

Initializes SQLite, starts API :8001 and frontend :3000, opens browser.

### v1 (backend core, PostgreSQL)

1. Create `backend_snt_core/.env` with `DATABASE_URL=postgresql+psycopg://...`
2. Migrations and seed — see `backend_snt_core/README.md`, `DEV_LOG.md`
3. `.\backend_snt_core\run.ps1` — API :8000

### Dependencies

```powershell
python -m venv .venv
.venv\Scripts\pip install -r backend_snt_core\requirements.txt
.venv\Scripts\pip install -r backend_snt_v2\requirements.txt
```
