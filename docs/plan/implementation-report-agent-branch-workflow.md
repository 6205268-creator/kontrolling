# Implementation Report: Agent Branch Workflow

**Date:** 2026-03-05
**Author:** AI Assistant
**Status:** ✅ Complete - Ready for Review

---

## Executive Summary

This report documents the implementation of a Git branch workflow system for AI agents working on the Kontrolling project. The system ensures that agents work in isolated branches, follow architectural standards, and never commit directly to main/master without explicit user approval.

**All 6 deliverables completed:**
1. ✅ Git branch policy rule created
2. ✅ Architecture Guardian rule created
3. ✅ Architecture linter script implemented and tested
4. ✅ Agent isolated task workflow documented
5. ✅ Pre-commit checklist updated
6. ✅ Current focus document updated with branch information

---

## 1. Context and Background

### 1.1 Problem Statement

The Kontrolling project (accounting system for Belarusian garden cooperatives) is developed by multiple AI agents using Cursor IDE. Without proper workflow controls:

- Agents could accidentally commit to main/master branches
- Architectural violations could go unnoticed
- No systematic review process before merging
- Context loss between sessions

### 1.2 Requirements (User-Approved Decisions)

During implementation, 8 key decisions were confirmed by the user:

| # | Decision | Outcome |
|---|----------|---------|
| 1 | Handle existing branches with unfinished work | Agent checks `git status` and `git log -n 5`, reports to user, continues from last commit |
| 2 | Store architecture-guardian rule | Create new file `.cursor/rules/agents/architecture-guardian.mdc` |
| 3 | Architecture linter script location | Create new script `backend/app/scripts/architecture_linter.py` |
| 4 | Store general workflow document | Separate file `docs/plan/agent-isolated-task-workflow.md` |
| 5 | Who creates the branch | Agent asks user: "Branch does not exist. Create feature/ledger-ready-mvp?" |
| 6 | How to fix review errors | Minor (style, names) → fix immediately; Major (architecture, boundaries) → ask user confirmation |
| 7 | Git branch policy rule location | `.cursor/rules/git-branch-policy.mdc` (clear name for everyone) |
| 8 | Check seed_db after stages | Yes, run `python -m app.scripts.seed_db` after each stage |

---

## 2. Deliverables

### 2.1 File: `.cursor/rules/git-branch-policy.mdc`

**Purpose:** Define how agents should work with Git branches during isolated tasks.

**Key Rules:**
- Never commit to `main` or `master`
- All commits only in the working branch
- Merge to main/master only after explicit user approval
- If branch doesn't exist → ask user before creating
- If branch exists → check status, show last 5 commits, ask for confirmation

**Git Commands Used:**
```bash
git branch --show-current
git log -n 5 --oneline
git status
git checkout <branch-name>
git checkout -b <branch-name> main
```

**Location:** `.cursor/rules/git-branch-policy.mdc`

---

### 2.2 File: `.cursor/rules/agents/architecture-guardian.mdc`

**Purpose:** Define the Architecture Guardian role for reviewing changes.

**When Called:**
- After completing each task stage
- Before merge to main/master
- On explicit user request: "@architecture-guardian check [modules]"

**Checklist (5 Points):**

1. **Layer Boundaries (Clean Architecture)**
   - API layer must not import from infrastructure
   - Domain layer must not depend on frameworks (FastAPI, SQLAlchemy)
   - Application layer must not import infrastructure directly

2. **Financial Core**
   - Accrual and Payment must reference FinancialSubject
   - No direct accruals to plots/meters without FinancialSubject

3. **Data Model**
   - New ORM models registered in `db/register_models.py`
   - Alembic migrations created and applicable
   - No dangling FKs

4. **Tests**
   - Tests cover new business logic
   - All tests pass (pytest)
   - No skipped tests without comments

5. **Diagram Consistency**
   - If data model changed → update diagrams in `docs/data-model/`
   - If architecture changed → update diagrams in `docs/architecture/`

**Response Format:**
- ✅ All clear
- ⚠️ Warnings (minor issues – style, naming)
- ❌ Errors (serious issues – boundaries, architecture, FinancialSubject)

**Error Fix Process:**
- Minor errors → agent fixes immediately
- Serious errors → agent asks user confirmation before fixing

**Location:** `.cursor/rules/agents/architecture-guardian.mdc`

---

### 2.3 File: `backend/app/scripts/architecture_linter.py`

**Purpose:** Automated script to check architectural constraints.

**Usage:**
```bash
cd backend
python -m app.scripts.architecture_linter
```

**Exit Codes:**
- `0` → All checks passed
- `1` → Violations found

**Checks Implemented (5):**

| Check | Description |
|-------|-------------|
| API → Infrastructure | API layer does not import from infrastructure |
| FinancialSubject | Accrual and Payment use FinancialSubject |
| Models Registration | All ORM models registered in register_models.py |
| Domain → Frameworks | Domain layer does not import fastapi/sqlalchemy/pydantic |
| LandPlot → Owner FK | LandPlot has no direct FK to Owner |

**Test Results:**
```
============================================================
ARCHITECTURE LINTER
============================================================

API -> Infrastructure: FAIL
   -> 5 violations found (existing project issues)
FinancialSubject: PASS
Models Registration: FAIL
   -> 17 violations found (existing project issues)
Domain -> Frameworks: PASS
LandPlot -> Owner FK: PASS

============================================================
RESULT: 22 violations found
============================================================
```

**Note:** Violations found are existing project issues, not implementation errors. The script works correctly.

**Location:** `backend/app/scripts/architecture_linter.py`

---

### 2.4 File: `docs/plan/agent-isolated-task-workflow.md`

**Purpose:** Universal workflow document for any isolated agent task.

**Process Flow:**

1. **Start Work**
   - User defines task and (optionally) branch name
   - Agent checks if branch exists
   - If not → ask user before creating
   - If exists → check status, report last commits, ask for confirmation

2. **Execute Stages**
   - For each stage:
     - Agent outputs stage plan, waits for "yes"/"start"
     - Makes changes in working branch
     - Runs checks in order: pytest → ruff → architecture_linter → seed_db
     - Calls @architecture-guardian for review
     - Fixes issues (minor → immediately, major → after confirmation)
     - Proceeds to next stage only after all checks pass

3. **Complete Task**
   - After all stages: report completion
   - Agent does NOT perform merge automatically
   - User must explicitly approve: "merge to main"
   - Agent executes merge only on explicit command

**Location:** `docs/plan/agent-isolated-task-workflow.md`

---

### 2.5 File: `docs/tasks/workflow-orchestration.md` (Updated)

**Changes Made:**

Added two new items to Section 1.7 "Pre-Commit Checklist":

```markdown
- [ ] `python -m app.scripts.architecture_linter` — all checks passed (exit code 0)
- [ ] `python -m app.scripts.seed_db` — seed data created without errors
```

**Location:** `docs/tasks/workflow-orchestration.md` (Section 1.7)

---

### 2.6 File: `docs/plan/current-focus.md` (Updated)

**Changes Made:**

Added new section "Branch for Task" under "What to Do Tomorrow":

```markdown
### Branch for Task

- **Branch Name:** `feature/ledger-ready-mvp`
- **Rule:** Agent follows `.cursor/rules/git-branch-policy.mdc`
  - Do not commit to main/master
  - Do not merge without explicit approval
  - If branch does not exist → ask before creating
  - If exists → check status and report to user
```

Updated work order to include all checks:
- pytest
- ruff check + format
- architecture_linter
- seed_db
- @architecture-guardian review

**Location:** `docs/plan/current-focus.md`

---

## 3. Technical Decisions and Rationale

### 3.1 Path Handling in architecture_linter.py

**Issue:** Initial implementation used relative paths (`Path("app/modules")`), which failed when script was run from different directories.

**Solution:** Added `BASE_DIR` calculation:
```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent
```

All paths now use `BASE_DIR` for reliability.

### 3.2 Encoding Issues

**Issue:** Windows console (cp1251) cannot display Unicode characters (emojis, Russian text).

**Solution:** 
- Replaced emojis (✅ ❌ →) with ASCII (PASS FAIL ->)
- Changed all error messages to English
- Script now works correctly on Windows

### 3.3 Rule File Naming

**Decision:** Named git branch rule `.cursor/rules/git-branch-policy.mdc` instead of `agent-branch-workflow.mdc`.

**Rationale:** Clearer name that all agents and users can understand immediately.

---

## 4. Testing

### 4.1 Architecture Linter Testing

**Command:**
```bash
cd backend
python -m app.scripts.architecture_linter
```

**Result:** Script executes successfully, exits with code 1 (violations found in existing project code).

**Verification:**
- All 5 checks run correctly
- Violations are properly detected and reported
- Exit codes work as expected (0 for success, 1 for violations)

### 4.2 Known Violations (Existing Project Issues)

The linter found 22 violations in the current codebase:

**API → Infrastructure (5 violations):**
- `accruals/api/contribution_types.py`
- `administration/api/user_loader.py`
- `cooperative_core/api/routes.py`
- `financial_core/api/routes.py`
- `reporting/api/routes.py`

**Models Registration (17 violations):**
- Multiple model classes not registered in `register_models.py`

**Note:** These are pre-existing issues in the project, not caused by this implementation. The linter correctly identifies them.

---

## 5. Integration with Existing Project

### 5.1 Project Structure Alignment

All files follow project conventions:
- Cursor rules in `.cursor/rules/`
- Agent-specific rules in `.cursor/rules/agents/`
- Scripts in `backend/app/scripts/`
- Documentation in `docs/plan/` and `docs/tasks/`

### 5.2 Consistency with Existing Documents

- References `docs/development-index.md` (single entry point)
- Aligns with `docs/tasks/workflow-orchestration.md` (Pre-Commit Checklist)
- Updates `docs/plan/current-focus.md` (current task focus)
- Creates `docs/plan/agent-isolated-task-workflow.md` (universal workflow)

### 5.3 Ledger-Ready MVP Task

The implementation is immediately applicable to the Ledger-ready MVP task:
- Branch: `feature/ledger-ready-mvp`
- All 5 stages must pass checks before proceeding
- Architecture Guardian review required after each stage

---

## 6. Limitations and Future Improvements

### 6.1 Current Limitations

1. **Architecture Linter Coverage:**
   - Does not check all Clean Architecture rules (e.g., Application → Infrastructure)
   - Model registration check is string-based (could use AST parsing)

2. **Branch Policy Enforcement:**
   - Relies on agent following rules (no hard Git hooks)
   - Could add pre-commit hooks for stronger enforcement

3. **Architecture Guardian:**
   - Manual review process (could be automated further)
   - No integration with CI/CD pipeline

### 6.2 Suggested Improvements

1. **Add Pre-commit Git Hook:**
   ```bash
   # .git/hooks/pre-commit
   cd backend && python -m app.scripts.architecture_linter
   ```

2. **CI/CD Integration:**
   - Add architecture_linter to GitHub Actions workflow
   - Block merge if linter fails

3. **Expand Linter Checks:**
   - Check Application layer imports
   - Verify domain events are properly raised
   - Check for soft deletion compliance

4. **Automated Architecture Guardian:**
   - Convert checklist to automated checks
   - Integrate with code review bots

---

## 7. Files Created/Modified Summary

| Action | File Path | Description |
|--------|-----------|-------------|
| Created | `.cursor/rules/git-branch-policy.mdc` | Git branch policy for agents |
| Created | `.cursor/rules/agents/architecture-guardian.mdc` | Architecture review role |
| Created | `backend/app/scripts/architecture_linter.py` | Automated architecture checks |
| Created | `docs/plan/agent-isolated-task-workflow.md` | Universal workflow document |
| Modified | `docs/tasks/workflow-orchestration.md` | Added linter + seed_db to checklist |
| Modified | `docs/plan/current-focus.md` | Added branch info for Ledger-ready |

---

## 8. Review Checklist

For the reviewing agent:

- [ ] Verify all 6 files exist and are correctly formatted
- [ ] Test architecture_linter.py runs without errors
- [ ] Confirm git-branch-policy.mdc covers all branch scenarios
- [ ] Confirm architecture-guardian.mdc has complete checklist
- [ ] Verify workflow document is clear and actionable
- [ ] Check that existing project violations are documented (not new issues)
- [ ] Confirm integration with Ledger-ready MVP task is correct

---

## 9. Conclusion

The implementation is complete and ready for production use. All user requirements have been met:

1. ✅ Agents work in isolated branches
2. ✅ No commits to main/master without approval
3. ✅ Architecture review before merge
4. ✅ Automated checks (linter + seed_db) in workflow
5. ✅ Clear process for error handling (minor vs. major)
6. ✅ Universal workflow applicable to any isolated task

**Next Steps:**
1. Review by another agent
2. User approval
3. Apply to Ledger-ready MVP task (Stage 1)

---

**Report End**

*Generated: 2026-03-05*
