---
name: plan-execution-docs-consolidation
description: Use when executing the "Single development index and roadmap" plan (or similar multi-stage docs consolidation). Ensures stage-by-stage execution, reference updates after file moves, checklist discipline, and no invented content. Essential for agents (e.g. Qwen/Gwen) running documentation restructure plans.
---

# Plan Execution: Documentation Consolidation

## When to Use This Skill

- User asks to "execute the plan", "выполнить план", or run the single development index / roadmap plan
- Task involves moving many files, merging folders (`tasks/` → `docs/tasks/`, `.memory-bank/` → `docs/`), and updating references across the repo
- Plan has numbered stages and a checklist; success depends on order and completeness

## Core Rules

1. **Execute by stage, not all at once.** One session = one stage (or one clear sub-stage). Do not run Stage 1 + 2 + 3 in a single run unless the user explicitly asks.
2. **Checklist is law.** Before finishing a stage, verify every checklist item for that stage. Use TodoWrite to track items; mark done only when the work is verified.
3. **After every move: update references.** When you move or rename a file, search the repo for old paths and update them (e.g. `tasks/e2e-setup.md` → `docs/tasks/e2e-setup.md` in `docs/review-report.md`, AGENTS.md, workflow-orchestration.mdc).
4. **Do not invent content.** If the plan says "по шаблону" or "по формату" — find the existing template/format in the repo and follow it. If a template is missing, list what's missing and ask instead of guessing.
5. **Delete only after checks.** Before deleting a folder (e.g. `logs/`): do the review step (e.g. 3.12.0 — check for decisions not in DECISIONS_LOG). Move critical items first, then delete.

## Plan Location and Structure

- **Plan file:** `docs/plan/single_development_index_and_roadmap.plan.md` (or the plan file the user attached).
- **Stages:** 1 (critical fixes) → 2 (GAPS sync) → 3 (consolidation: moves + deletes) → 4 (create index) → 5 (AGENTS.md + README) → 6 (Cursor rule).
- **Dependency:** Stage 4.3 (write "Топ-5" section) must be done only after Stage 1 is complete.

## Workflow for Each Stage

```
1. Read the plan section for the current stage and its checklist.
2. TodoWrite: create todos from the checklist items for this stage.
3. Do the work in the order given (moves first, then reference updates, then deletes).
4. After each move: grep for old path → update all references.
5. Verify checklist; mark todos complete. Report what was done and what (if anything) is left for the next stage.
```

## Reference-Update Shortcuts (This Plan)

| Moved / Removed | Update references in |
|-----------------|----------------------|
| `tasks/*` → `docs/tasks/*` | `workflow-orchestration.mdc` (paths + frontmatter `globs`), `docs/review-report.md`, AGENTS.md, any doc linking to `tasks/` |
| `.memory-bank/productContext.md` → `docs/product-context.md` | Internal links inside `docs/product-context.md` (projectbrief.md → remove, systemPatterns → `docs/architecture/system-patterns.md`) |
| `docs/agents/` → `.cursor/rules/agents/` | AGENTS.md, README.md, development-index.md (once created) |
| `.memory-bank/` removed | Any remaining links to `.memory-bank/` |

## Red Flags — STOP and Fix

- Running two or more full stages in one reply without being asked
- Moving a file without searching for and updating references to the old path
- Deleting `logs/` or `.memory-bank/` before doing the review step (3.12.0, 3.1.1)
- Writing RESOLVED_GAPS or PENDING_GAPS entries without following the existing template/style in the repo
- Inventing a "template" when the plan says "по шаблону" and the repo has one — use the repo's

## Language

- Follow project convention: **Russian** for user-facing content and plan-related messages unless the user asks otherwise (see AGENTS.md / project rules).
- Keep file names and code paths in English as in the plan.

## When NOT to Use This Skill

- Implementing features (use vue-development or backend skills)
- One-off doc edits with no plan
- When the user only asked a question about the plan (answer, do not execute)
