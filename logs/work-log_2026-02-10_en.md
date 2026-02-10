# Work log (English, technical)

**Created:** 2026-02-10  
**Purpose:** technical log for AI context. Same events as `work-log_2026-02-10_ru.md`, in English. Add entries when user says "record it" / "запиши".

---

## Entries

### Entry 1 — 2026-02-10 (data model: PlotOwnership, plot ownership by period and share)

**Summary:**

1. **Problem:** A land plot (LandPlot) can have different owners over time; at a given moment there can be multiple owners with shares (half, third, etc.). A direct LandPlot → Owner link was insufficient.

2. **New entity PlotOwnership (plot ownership / share):**
   - Link plot ↔ owner with validity period (`valid_from`, `valid_to`) and share.
   - Share stored as fraction: `share_numerator` / `share_denominator` (1 = full plot, 1/2 = half, 1/3 = third).
   - By date we can determine who owned the plot in that period and with what share; multiple owners in one period allowed (shares sum to 1).

3. **LandPlot changes:** Attribute `owner_id` removed. Plot ownership is defined only via PlotOwnership. "No owner" = no PlotOwnership records for the given date.

4. **Updated artifacts:**
   - `docs/source-material/model-data.txt` — conceptual model (entities, relationships, constraints).
   - `docs/data-model/entities-minimal.md` — minimal entity set, relationship table.
   - `docs/data-model/schema-viewer.html` — visual schema: PlotOwnership node, PlotOwnership → LandPlot and PlotOwnership → Owner edges; LandPlot → Owner edge removed.

5. **Sync:** Model and schema aligned; PlotOwnership moved from "planned for later" into core.

---

*Folder `logs/` is used for architecture and other activity logs.*
