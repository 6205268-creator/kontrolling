# v2 Implementation Plan: physical persons, SNT members, plots

Before implementation, follow **only** items in this plan. Log all changes in `CHANGELOG_IMPLEMENTATION.md`.

---

## Goals

- **Backend v2:** schema per `ARCHITECTURE_SNT_V2_PHYSICAL_PERSON.md`: `physical_person`, `snt`, `snt_member`, `plot`, `plot_owner`. No meter, charge_item, or documents — refbooks and links only.
- **Frontend:** SNT selector; on SNT change, “per selected SNT” mode. Sections: **Physical persons**, **SNT members**, **Plots**. Click person → show memberships (which SNTs, periods) and plots (which, periods). View‑only + seed data; no add/edit.
- **Style:** minimal, modern, simple icons.

---

## Phase 1. Plan and log

| # | Action | Files |
|---|--------|-------|
| 1.1 | Create and save plan | `PLAN_V2_IMPLEMENTATION.md` |
| 1.2 | Create changelog | `CHANGELOG_IMPLEMENTATION.md` |

---

## Phase 2. Backend v2

**Location:** separate folder `backend_snt_v2` (do not change `backend_snt_core`).

**DB:** SQLite (`snt_v2.db` in `backend_snt_v2` root) so demo does not require PostgreSQL.

| # | Action | Details |
|---|--------|---------|
| 2.1 | Project layout | `app/`, `alembic/`, `requirements.txt`, `alembic.ini`, `run.ps1` |
| 2.2 | SQLAlchemy models | `physical_person`, `snt`, `snt_member`, `plot`, `plot_owner` per v2 |
| 2.3 | Alembic | Configure for SQLite; migration `0001_init_v2` creates all tables |
| 2.4 | Seed | `scripts/seed.py`: 2–3 SNTs, 6–8 physical persons, memberships, plots, owners; at least one person with multiple plots and/or memberships |
| 2.5 | REST API | FastAPI. Endpoints: `GET /snts`, `/physical-persons`, `/snt-members?snt_id=`, `/plots?snt_id=`, `GET /physical-persons/{id}` (with members, plot_owners). CORS for frontend |
| 2.6 | Run | `run.ps1`: migrations → seed → uvicorn on :8001 |

---

## Phase 3. Frontend

**Location:** existing `frontend/`. Adapt for v2 without full rewrite.

| # | Action | Details |
|---|--------|---------|
| 3.1 | API client | Base URL `http://localhost:8001`. Load SNTs, physical persons, members by `snt_id`, plots by `snt_id`, person by `id` with links |
| 3.2 | SNT selector | Dropdown in header from `GET /snts`; on change, reload members and plots |
| 3.3 | Nav | Sections: **Overview** (summary per SNT), **Physical persons**, **SNT members**, **Plots**. Hide or temporarily remove “Documents”, “Reports” |
| 3.4 | Overview | Cards: counts of persons, members, plots. Minimal text |
| 3.5 | Physical persons | Table/cards. Row click → detail (modal or side panel): name, phone, INN; “Memberships” (SNT, period); “Plots” (number, SNT, period) |
| 3.6 | SNT members | List, filter by selected SNT. Columns: person, join date, leave date. View only |
| 3.7 | Plots | List by selected SNT. Number, optional current owner. View only |
| 3.8 | Style | Minimal: neutral palette, space, simple icons. Keep light/dark theme toggle |

---

## Phase 4. Changelog

| # | Action | Details |
|---|--------|---------|
| 4.1 | Format | Each notable change: date (UTC), short description, files |
| 4.2 | Required | Any create/change/delete under the plan → log in `CHANGELOG_IMPLEMENTATION.md` |

---

## Order

1. Phase 1 (plan + log).
2. Phase 2 (backend v2) fully.
3. Phase 3 (frontend) fully.
4. Phase 4 — in parallel with 2 and 3.

---

## Outcome

- Backend v2 on SQLite at `http://localhost:8001`.
- Frontend: SNT selector, physical persons, members, plots; person click → memberships and plots.
- View‑only, seed data. All changes in `CHANGELOG_IMPLEMENTATION.md`.
