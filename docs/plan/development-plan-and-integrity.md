# План разработки и целостность системы

**Назначение:** единый документ по тому, как вести разработку без «метаний», как сохранять целостность системы и как устроена проверка изменений (в т.ч. агентами).  
**Расположение:** `docs/plan/development-plan-and-integrity.md` — единственное место для этой темы; обновлять только здесь.  
**Дата:** 2026-03-04

---

## 1. Как не «метаться из стороны в сторону»

### Что уже есть

- **Единая точка входа:** [`docs/development-index.md`](../development-index.md) (правило `development-index-rule.mdc`, alwaysApply: true).
- **Топ-5** в индексе — приоритизированный список «что делать сейчас».
- **Иерархия «что дальше»:** индекс (Топ-5) → `project-implementation.md` (фичи) → `PENDING_GAPS.md` (дыры) → `docs/tasks/` (задания).
- **Правило:** открыть индекс → взять задачу из Топ-5 → работать. При конфликте данных приоритет у `docs/` и `AGENTS.md`.

### Порядок работы

- **План:** нетривиальные задачи (3+ шага или архитектура) — план в `docs/tasks/todo.md` с проверяемыми пунктами ([`docs/tasks/workflow-orchestration.md`](../tasks/workflow-orchestration.md)).
- **Порядок агентов:** Architecture (project-orchestrator) → затем Backend / DevOps ([`agent-team-tasks-order.mdc`](../../.cursor/rules/agents/agent-team-tasks-order.mdc)).
- **Фичи:** одна фича за раз по [`docs/context-tree/feature-workflow-prompt.md`](../context-tree/feature-workflow-prompt.md): контекст из Fxx.md → выполнение → итог и подтверждение пользователя → отметка в `project-implementation.md` и создание Fxx-vN-date.md.

---

## 2. Как сохраняется целостность системы

| Механизм | Где | Что даёт |
|----------|-----|----------|
| Одна очередь фич | `project-implementation.md` + feature-workflow | Следующая фича — первая без ✅; контекст только из своего Fxx. |
| Границы архитектуры | [`system-patterns.md`](../architecture/system-patterns.md), Clean Architecture | Модули, зависимости внутрь; API не импортирует Infrastructure. |
| Schema First | `.cursor/rules/architecture/` | Диаграммы/схема обновляются до кода. |
| Ограниченные пути | [`docs/architecture/OWNERSHIP.md`](../architecture/OWNERSHIP.md) | Глоссарии правит только Lead Architect. |
| ADR | [`docs/architecture/adr/README.md`](../architecture/adr/README.md) | Значимые решения фиксируются; утверждает Lead Architect. |
| Верификация перед «готово» | [`workflow-orchestration.md`](../tasks/workflow-orchestration.md) | Задача не «готово» без доказательства (тесты, логи). |
| CI | `.github/workflows/backend-tests.yml` | На push/PR: pytest + ruff + architecture linter; сломанные тесты или линт блокируют слияние. |
| Приоритет источников | development-index-rule | При конфликте: docs/ и AGENTS.md > .cursor/rules/. |

---

## 3. Агент, отслеживающий изменения других (арбитр)

### Текущее состояние

- **project-orchestrator** — может ревьюить и отклонять результаты других агентов; вызывается **вручную**.
- **qa-engineer** — проверка и регрессия после фичи; вызывается **вручную**.
- **Автоматического** агента, который проверяет каждое изменение на соответствие правилам и стандартам, **нет**. CI проверяет тесты, ruff и architecture linter (архитектурные границы).

### Рекомендация

Формализовать вызов ревью: для задач, затрагивающих ADR, глоссарии, границы модулей или общие контракты, перед закрытием вызывать **project-orchestrator** для проверки по acceptance criteria и архитектурным правилам. При желании можно ввести явную роль «guardian» с тем же сценарием.

---

## 4. Предложения по дальнейшей работе

### Выполнено (2026-03-04)

1. **✅ Чек-лист перед «готово»** — добавлен в [`docs/tasks/workflow-orchestration.md`](../tasks/workflow-orchestration.md) (раздел 1.7 Pre-Commit Checklist)
2. **✅ Секция «Целостность системы»** — добавлена в [`docs/development-index.md`](../development-index.md) (секция 4.12)
3. **✅ Роль «architecture-guardian»** — создана в [`.cursor/rules/architecture-guardian.mdc`](../../.cursor/rules/architecture-guardian.mdc)
4. **✅ Архитектурный линтер** — создан скрипт [`backend/app/scripts/architecture_linter.py`](../../backend/app/scripts/architecture_linter.py)

### Осталось

5. **Pre-commit или CI-job** — проверить, что в `docs/architecture/glossary/` не коммитят без разрешения (через CODEOWNERS)

---

## 6. Автоматизация

### Архитектурный линтер

**Запуск:**
```bash
cd backend
python -m app.scripts.architecture_linter
```

**Где запускается:** CI (GitHub Actions) и опционально pre-commit (`backend/.pre-commit-config.yaml`).

**Проверяет:**
- API не импортирует infrastructure (в т.ч. infrastructure.models)
- Accrual и Payment используют FinancialSubject
- Модели зарегистрированы в `db/register_models.py`
- Domain не импортирует fastapi/sqlalchemy/pydantic
- LandPlot не имеет прямого FK на Owner (только через PlotOwnership)

**Текущие нарушения (требуют исправления):**
- `accruals/api/contribution_types.py` — импортирует infrastructure.repositories
- `cooperative_core/api/routes.py` — импортирует infrastructure.repositories

**Правильный паттерн** (как в `payments/api/routes.py`):
```python
from app.modules.deps import get_create_accrual_use_case
```

**Идеи по развитию (backlog):**
| Идея | Зачем |
|------|--------|
| Application → Infrastructure | Проверять, что слой application не импортирует infrastructure (сейчас только API). |
| Soft-delete для финансов | Accrual/Payment/Expense не hard-delete, а status archived/cancelled — проверять наличие. |
| Вывод в JSON | Флаг `--format=json` для CI/скриптов. |
| Только изменённые файлы | Режим «проверить только изменённые файлы» для быстрого pre-commit. |

### Architecture Guardian

**Вызов:**
```
@architecture-guardian Проверь изменения в модуле accruals
```

**Чек-лист:** 8 пунктов (границы, FinancialSubject, модель, термины, тесты, ADR)

---

## 7. Где что лежит

| Вопрос | Документ |
|--------|----------|
| Что делать сейчас? | [`docs/development-index.md`](../development-index.md) → Топ-5 |
| **Где остановились и что делать завтра? (контекст сессии)** | **[`docs/plan/current-focus.md`](current-focus.md)** |
| Как вести задачу? | [`docs/tasks/workflow-orchestration.md`](../tasks/workflow-orchestration.md), `docs/tasks/todo.md` |
| Как делать фичу? | [`docs/context-tree/feature-workflow-prompt.md`](../context-tree/feature-workflow-prompt.md) |
| Кто что может менять? | [`docs/architecture/OWNERSHIP.md`](../architecture/OWNERSHIP.md) |
| Архитектурные решения? | [`docs/architecture/adr/README.md`](../architecture/adr/README.md) |
| **План разработки и целостность (этот документ)** | `docs/plan/development-plan-and-integrity.md` |

---

*Обновлять этот файл при изменении процесса разработки или правил целостности. Владелец: Lead Architect или по согласованию.*
