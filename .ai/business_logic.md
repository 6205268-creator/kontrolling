# Business logic

## Domain entities

### v2 (current UI backend)

| Entity | Table | Description |
|--------|-------|-------------|
| **Physical person** | `physical_person` | Real person; global, not tied to an SNT. Source of all payments. |
| **SNT** | `snt` | Gardening association (tenant). |
| **SNT member** | `snt_member` | Membership: SNT + physical person over a period. Key `(snt_id, physical_person_id, date_from)`. Re‑joining = new row. |
| **Plot** | `plot` | Plot in an SNT. `UNIQUE (snt_id, number)`. |
| **Plot owner** | `plot_owner` | Plot ↔ physical person over a period. One person can own many plots; one plot can have different owners over time. |
| **Meter** | `meter` | Meter on a plot. `meter_type`: `electricity`, `water`. `UNIQUE (snt_id, plot_id, meter_type)`. |
| **App user** | `app_user` | Login identity. `role`: `admin` \| `snt_user`; `snt_id` set for `snt_user`. |

### v1 (core; documents, registers)

- `owner` (per‑SNT “owner”), `plot_owner` (plot ↔ owner), `charge_item`, `doc_accrual` / `doc_accrual_row`, `doc_payment` / `doc_payment_row`, `reg_balance`.

---

## Business rules

- **Membership:** Joining → new `snt_member` row. Leaving → set `date_to`. Re‑joining → new row (new membership).
- **Payments:** Always by **physical person**. As **member** → member fees; as **plot owner** → utilities (electricity, water, etc.) via meters.
- **Meters:** One meter per type per plot (`snt_id`, `plot_id`, `meter_type` unique).
- **App users:**  
  - **admin:** sees all SNTs, can switch SNT.  
  - **snt_user:** sees only their SNT (`user.snt_id`). No SNT switcher; no access to other SNTs’ data.

**v1:** Documents have `is_posted`. Only posted documents generate `reg_balance` movements. Posting recalculates movements; unposting removes them.

---

## Workflows

### v2

- **View data:** Choose user → (if admin) choose SNT → load members, plots, meters, physical persons for that SNT. Inspect physical person → modal with memberships and plot ownerships.
- **User switch:** Reload `/me`, then `/snts` and section data. For `snt_user`, always use their single SNT.

### v1 (core)

- **Post document:** 1) Start transaction. 2) Delete old `reg_balance` rows for that document. 3) Compute new movements from document rows. 4) Insert into `reg_balance`. 5) Set `is_posted = TRUE`. 6) Commit.
- **Unpost:** 1) Start transaction. 2) Delete `reg_balance` rows for document. 3) Set `is_posted = FALSE`. 4) Commit. No compensating entries.

---

## Calculations

- **v2:** No calculations. Counts (members, plots, meters) are from list lengths; no stored aggregates.
- **v1:** `reg_balance` movements: accruals → `amount_debit = amount`, `amount_credit = 0`; payments → `amount_debit = 0`, `amount_credit = amount`. Balance and reports derive from `reg_balance` (e.g. `GET /reports/balance?on_date=`).
