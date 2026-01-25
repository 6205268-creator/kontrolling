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

---

# v1 Core Architecture

This document describes a 1C‑like recalculation‑based accounting model for SNT (gardening associations), implemented on PostgreSQL + FastAPI + SQLAlchemy. Suited for Obsidian (sections, links, clear entity structure).

---

## 1. General concept

- **System core** = PostgreSQL (data) + business logic on backend.
- **UI and frontend are not the source of truth** and can be fully disabled.
- All calculations and invariants are enforced in the core:
  - DB structure (FK, CHECK, UNIQUE, NOT NULL);
  - transactions;
  - posting/unposting services.

The system has 3 data layers:

1. **Primary data:** refbooks, documents, document rows.
2. **Derived data:** registers (movements), recalculated from documents.
3. **Document state:** `is_posted` flag (posted / not posted).

---

## 2. Multi‑tenant model (SNT)

- **All tables** have `snt_id`.
- Missing `snt_id` is an architectural error.
- Main tenant entity: table `snt`.
- Data of different SNTs do not mix; Row Level Security can be enabled if needed.

---

## 3. Data structure

### 3.1. Refbooks (primary data)

- `snt`
  - `id` (PK)
  - `name`
  - `created_at`, `updated_at`

- `plot` (plots)
  - `id` (PK)
  - `snt_id` (FK → `snt`)
  - `number` (plot number/label)
  - other attributes as needed

- `owner` (owners)
  - `id` (PK)
  - `snt_id` (FK → `snt`)
  - name, INN, etc.

- `plot_owner` (plot–owner link)
  - `id` (PK)
  - `snt_id` (FK → `snt`)
  - `plot_id` (FK → `plot`)
  - `owner_id` (FK → `owner`)
  - validity period (from/to dates)

- `charge_item` (charge types / services)
  - `id` (PK)
  - `snt_id` (FK → `snt`)
  - `name`
  - `type` (member fee, target, service, etc.)

All refbooks:

- have `snt_id NOT NULL`;
- are indexed on `snt_id`;
- are linked via `FOREIGN KEY`.

---

## 4. Documents and document rows

### 4.1. General rules

- Document:
  - has unique `id`;
  - belongs to exactly one SNT (`snt_id`);
  - has `is_posted` state flag;
  - stores only user‑entered data (no derived calculations).

- Document rows:
  - are primary data;
  - always reference document and SNT;
  - contain no derived totals.

### 4.2. First‑increment documents

**Accrual document** (`doc_accrual`):

- Header: `id`, `snt_id` (FK → `snt`), `number`, `date`, `is_posted`.
- Rows `doc_accrual_row`: `id`, `snt_id`, `doc_id` (FK → `doc_accrual`), `plot_id`, `charge_item_id`, `amount`; optionally `period_from`, `period_to`.

**Payment document** (`doc_payment`):

- Header: `id`, `snt_id`, `number`, `date`, `is_posted`.
- Rows `doc_payment_row`: `id`, `snt_id`, `doc_id` (FK → `doc_payment`), `plot_id` and/or `owner_id`, `charge_item_id`, `amount`.

Invariant: row `snt_id` = document `snt_id`; enforced via FK/constraints/trigger in DB.

---

## 5. Registers (derived data)

### 5.1. General rules

- Register holds **only derived data**.
- Each register row:
  - always references a document;
  - always references a document row;
  - cannot exist without them;
  - is fully recalculated on posting.

### 5.2. Settlements register (`reg_balance`)

Purpose: store accrual/payment movements by plot/owner/charge_item.

Fields: `id`, `snt_id`, `document_id`, `document_row_id`, `document_type` (e.g. `ACCRUAL`, `PAYMENT`), `date`, `plot_id`, `owner_id` (optional), `charge_item_id`, `amount_debit`, `amount_credit`.

Rules: accruals → `amount_debit = amount`, `amount_credit = 0`; payments → `amount_debit = 0`, `amount_credit = amount`.

---

## 6. Posting and unposting

### 6.1. Post document

1. Begin transaction.
2. Delete all existing register rows for `document_id` (and `document_type`).
3. Compute new movements from document and rows.
4. Insert into registers.
5. Set `is_posted = TRUE`.
6. Commit. On error, rollback.

### 6.2. Unpost

1. Begin transaction.
2. Delete register rows for document.
3. Set `is_posted = FALSE`.
4. Commit. Document data kept; no compensating entries.

---

## 7. Backend (FastAPI + SQLAlchemy)

- **DB models:** match PostgreSQL tables; structure only, no business logic.
- **Domain services:** CRUD, posting/unposting/repost; follow the algorithms above.
- **REST API:** JSON in/out; no business logic; call services.

Frontend does not post, recalculate registers, or make architectural decisions.

---

## 8. Verifiability

Every business scenario must be:

- executable via SQL and backend only (no UI);
- understandable from DB schema and table/register queries;
- manually verifiable via pgAdmin/DBeaver/SQL console.

If a scenario cannot be explained in terms of SQL, the architecture is violated.

---

# v2 Architecture: Physical Person vs SNT Member

SNT member (membership) and physical person are **distinct entities**. Membership key: **SNT id + Physical person id** (+ period). One physical person can have multiple memberships (leave + re‑join = new membership), multiple plots, multiple meters, multiple payments.

---

## 1. Key entities

| Table | Description |
|-------|-------------|
| `physical_person` | Real person; global, not tied to an SNT. Source of all payments. |
| `snt` | Gardening association (tenant). |
| `snt_member` | Membership: SNT + physical person over a period. Leave → `date_to`; re‑join → new row. |
| `plot` | Plot in an SNT. |
| `plot_owner` | Plot ↔ physical person over a period. Who owns, when. |
| `meter` | Meter on a plot. Electricity, water, etc. |
| `charge_item` | Charge type / service: member fee, target, electricity, water, etc. |

**Who pays what (source of money = physical person):**

- As **SNT member** (via `snt_member`) → member fees.
- As **plot owner** (via `plot_owner`) → electricity, water, other consumption‑based services.

---

## 2. DB schema (tables, keys, links)

### 2.1. `physical_person`

Global; not tied to a specific SNT.

| Column | Type | Description |
|--------|-----|-------------|
| `id` | PK | Unique id |
| `full_name` | VARCHAR(250) NOT NULL | Full name |
| `inn` | VARCHAR(12) NULL | Tax id |
| `phone` | VARCHAR(50) NULL | Phone |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

Uniqueness: `id` PK. Optionally `inn` UNIQUE. Linked from `snt_member`, `plot_owner`, payment documents (payer).

### 2.2. `snt`

| Column | Type | Description |
|--------|-----|-------------|
| `id` | PK | |
| `name` | VARCHAR(200) NOT NULL UNIQUE | SNT name |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

### 2.3. `snt_member`

SNT + physical person over a period. Join → new row. Leave → `date_to`. Re‑join → new row.

| Column | Type | Description |
|--------|-----|-------------|
| `id` | PK | |
| `snt_id` | FK → `snt.id` | |
| `physical_person_id` | FK → `physical_person.id` | |
| `date_from` | DATE NOT NULL | Join date |
| `date_to` | DATE NULL | Leave date; NULL = current |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Uniqueness:** `UNIQUE (snt_id, physical_person_id, date_from)`. One person can have multiple `snt_member` rows per SNT (different periods). Membership key: `(snt_id, physical_person_id)` + `(date_from, date_to)`.

### 2.4. `plot`

| Column | Type | Description |
|--------|-----|-------------|
| `id` | PK | |
| `snt_id` | FK → `snt.id` | |
| `number` | VARCHAR(50) NOT NULL | Plot number |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Uniqueness:** `UNIQUE (snt_id, number)`.

### 2.5. `plot_owner`

Plot ↔ physical person over a period. One plot, different owners over time; one person, multiple plots.

| Column | Type | Description |
|--------|-----|-------------|
| `id` | PK | |
| `snt_id` | FK → `snt.id` | |
| `plot_id` | FK → `plot.id` | |
| `physical_person_id` | FK → `physical_person.id` | Owner |
| `date_from` | DATE NOT NULL | From |
| `date_to` | DATE NULL | To; NULL = current |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Uniqueness:** `UNIQUE (snt_id, plot_id, physical_person_id, date_from)`.

### 2.6. `meter`

Meter on a plot. Types: electricity, water, etc.

| Column | Type | Description |
|--------|-----|-------------|
| `id` | PK | |
| `snt_id` | FK → `snt.id` | |
| `plot_id` | FK → `plot.id` | |
| `meter_type` | VARCHAR(50) NOT NULL | `electricity`, `water`, etc. |
| `serial_number` | VARCHAR(100) NULL | |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Uniqueness:** `UNIQUE (snt_id, plot_id, meter_type)` — one meter per type per plot. Payments for electricity/water → plot owner (physical person via `plot_owner`).

### 2.7. `charge_item`

| Column | Type | Description |
|--------|-----|-------------|
| `id` | PK | |
| `snt_id` | FK → `snt.id` | |
| `name` | VARCHAR(250) NOT NULL | |
| `type` | VARCHAR(50) NOT NULL | `member_fee`, `target`, `service`, etc. |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

**Uniqueness:** `UNIQUE (snt_id, name)`.

---

## 3. Uniqueness summary

| Table | Constraint |
|-------|------------|
| `physical_person` | `id` PK |
| `snt` | `id` PK, `name` UNIQUE |
| `snt_member` | `UNIQUE (snt_id, physical_person_id, date_from)`; re‑join = new row |
| `plot` | `UNIQUE (snt_id, number)` |
| `plot_owner` | `UNIQUE (snt_id, plot_id, physical_person_id, date_from)` |
| `meter` | `UNIQUE (snt_id, plot_id, meter_type)` |
| `charge_item` | `UNIQUE (snt_id, name)` |

---

## 4. Accruals and payments (brief)

- **Accruals:** member fees → `snt_member`; electricity, water, etc. → `plot` + `meter`; responsible = plot owner.
- **Payments:** payer always **physical person** (`physical_person_id`). Optional links to `snt_member` and/or `plot_owner` per accounting rules.

Detail for document rows and registers can be in a separate section; multi‑tenant via `snt_id` everywhere.

---

## 5. Differences from v1

| v1 | v2 |
|----|-----|
| `owner` per SNT, effectively "member + owner" combined | **Physical person** (global) and **SNT member** (`snt_member`) separate; plot ownership in `plot_owner` |
| `plot_owner` links plot and `owner` | `plot_owner` links plot and **physical person** |
| No explicit membership history (leave/return) | Membership = `snt_member` with `date_from`/`date_to`; re‑join = new row |
| No meter entity | `meter` on plot; types electricity, water, etc. |
| Payer not formalized | **Physical person** is source of money; pays as member (fees) and as owner (plot services) |

Next step, if needed: concrete document tables (`doc_accrual`, `doc_payment`) and registers with `physical_person_id`, `snt_member_id`, `plot_owner_id` where appropriate.
