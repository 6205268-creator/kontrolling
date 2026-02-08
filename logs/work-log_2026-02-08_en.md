# Work log (English, technical)

**Created:** 2026-02-08  
**Purpose:** technical log for AI context. Same events as `work-log_2026-02-08_ru.md`, in English. Add entries when user says "record it" / "запиши".

---

## Entries

### Entry 1 — 2026-02-08 (first entry of the day)

**Summary:**

1. **Cursor rules** — Created `.cursor/rules/` with: project conventions (SOLID, KISS, Russian), AaC/C4 architecture, diagram rules (Mermaid only, naming, Schema First), guide workflow (ask permission, wait confirmation). Consolidated into `docs/project-rules.md` including: answer capabilities only / no auto-execution; show diagrams in chat as Markdown; no external browser.

2. **Project structure** — Created `docs/architecture/adr`, `common`, `glossary` and `domains/` (plots, contributions, meter_readings, bank_statements, notifications, reporting).

3. **Repository sync guide** — `docs/repository-sync-guide.md`: where to run commands (terminal), pull/push, rule that agent asks permission and waits for confirmation.

4. **Architecture and diagrams:**
   - Component library in `docs/architecture/common/`: actors, external systems, databases (`.mmd`).
   - L1 system context — КОНТРОЛЛИНГ, owners, chair, treasurer, bank, Telegram, email, SMS.
   - Glossary for domain «взносы» in `docs/architecture/glossary/contributions.md`.
   - ADR template in `docs/architecture/adr/ADR-template.md`.
   - L2 container diagram for «банковские выписки» in `domains/bank_statements/container-diagram.mmd`.

5. **Git (Option B — current repo):** Added `.gitignore` (Python + artifacts), `README.md` (КОНТРОЛЛИНГ, structure). Committed and pushed to `origin main`.

6. **GitHub Mermaid render error** — `.mmd` files contained markdown fences; renderer needs raw Mermaid only. Fixed: stripped fences from all `.mmd`. Added `docs/architecture/diagrams.md` with proper ```mermaid blocks for GitHub. Committed and pushed.

7. **Logs folder** — Created `logs/` and two work-log files with date in name: `work-log_2026-02-08_ru.md` (Russian), `work-log_2026-02-08_en.md` (English); entries added on user request.

### Entry 2 — 2026-02-08 (end of day)

8. **Logs and README on GitHub** — Committed and pushed `logs/`; added `/logs/` to root `README.md` structure.

9. **Mermaid extension in Cursor** — Installed `bierner.markdown-mermaid` for diagram preview in Markdown.

10. **Obsidian duplicate** — Created `obsidian/`: «КОНТРОЛЛИНГ — диаграммы.md» (same Mermaid diagrams) and `README.md` with how to open in Obsidian.

11. **Rules: question ≠ action** — Updated `docs/project-rules.md` and `.cursor/rules/guide-workflow.mdc`: if user **asks** («can we», «можно ли», etc.) — only answer, do nothing. Execute only on explicit request («сделай», «выполни», «подтверждаю»).

12. **Git sync** — All changes committed and pushed to `origin main`. Work for today finished.

---

*Folder `logs/` is used for architecture and other activity logs.*
