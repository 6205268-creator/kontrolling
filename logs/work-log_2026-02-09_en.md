# Work log (English, technical)

**Created:** 2026-02-09  
**Purpose:** technical log for AI context. Same events as `work-log_2026-02-09_ru.md`, in English. Add entries when user says "record it" / "запиши".

---

## Entries

### Entry 1 — 2026-02-09 (project design session, short break)

**Summary:**

1. **Project design document** — Created and updated `docs/project-design.md` as single source of truth for design decisions.

2. **Tech stack (fixed):**
   - Backend: Python, Django (REST API).
   - Database: PostgreSQL.
   - Frontend: React (SPA), no Next.js for now.
   - Architecture: separate frontend and backend; communication via REST API.

3. **Terminology and scope:** System is for **СТ** (садоводческое товарищество), Belarus legislation — not СНТ. Correct abbreviation: **СТ**.

4. **Deployment:** VPS in the cloud; Docker planned for later (distant future). No detailed design yet.

5. **Authorization:** Roles — administrator, treasurer, chairman. Login + password. 2FA deferred.

6. **Multi-tenancy:** System serves **several cooperatives (СТ)** in one instance. Data model must include a tenant key (or similar) in all main tables to isolate data per cooperative.

7. **Data model design approach:** Same as architecture — **Architecture as Code (AaC)**. Visual representation of entity relationships required (Mermaid diagrams in repo). Schema First. Process for designing the model to be agreed separately.

8. **Communication style rule** — Added `.cursor/rules/communication-style.mdc`: address user as "ты", partners tone, no over-formality, no over-familiarity.

9. **Research:** Checked existing solutions (1С:Садовод, SNT Club, open-source analogues) and frontend trends (React/Next.js vs Angular); recorded in conversation, not in project-design.

### Entry 2 — 2026-02-09 (data model, schema viewer, end of day)

10. **Data model prompt** — Saved `docs/data-model/conceptual-model-prompt.md` (goal, return format, warnings, context for conceptual model).

11. **Minimal entity set** — Created `docs/data-model/entities-minimal.md`: entities in English with Russian comments (Cooperative, Person, Member, LandPlot, PlotOwnership), relationship table, "planned for later" block.

12. **project-design updates:** Person scoped to one cooperative only; Person–Member 1:1; one person can own multiple plots; banks/counterparties as shared subsystem later.

13. **Schema viewer** — `docs/data-model/schema-viewer.html`: field-to-field links table (Access-style), interactive vis-network diagram with draggable nodes, FK labels on edges, Russian tooltips, layout persisted in browser. Approved by user.

14. **GitHub sync** — All changes committed and pushed. Work for today finished.

---

*Folder `logs/` is used for architecture and other activity logs.*
