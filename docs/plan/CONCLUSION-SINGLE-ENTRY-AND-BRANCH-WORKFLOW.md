# Вывод: единая точка входа и workflow веток

**Дата:** 2026-03-05  
**Вопрос:** Соблюдается ли в проекте запланированная структура (единая точка входа, версионирование, работа в ветке, merge только после одобрения)?

---

## 1. Краткий вывод

**Да, запланированное реализовано.** В проекте есть:

| Запланировано | Реализовано | Где |
|---------------|-------------|-----|
| Единая точка входа | ✅ | `docs/development-index.md` + правило `development-index-rule.mdc` (alwaysApply) |
| Версионирование / работа в ветке | ✅ | Правило `.cursor/rules/git-branch-policy.mdc`: не коммитить в main/master, merge только по явному одобрению |
| Изолированная задача в ветке | ✅ | Документ `docs/plan/agent-isolated-task-workflow.md` + ссылки из current-focus |
| Ревью перед merge | ✅ | Pre-Commit (pytest, ruff, architecture_linter, seed_db) + вызов @architecture-guardian по этапам |
| Контроль «где остановились» | ✅ | `docs/plan/current-focus.md`, ссылка из development-index |

Агент при изолированной задаче должен: открыть индекс → при необходимости current-focus → работать в указанной ветке → после этапов гонять проверки и ревью → merge только по твоей команде.

---

## 2. Что именно проверено

- **Единая точка входа:** В начале сессии и при вопросе «что делать?» правило предписывает открыть `docs/development-index.md`. Там Топ-5, дорожная карта, быстрые ссылки на current-focus и план целостности.
- **Ветки:** В `git-branch-policy.mdc` явно: не коммитить в main/master, не мержить без одобрения, при отсутствии ветки — спросить, при существующей — проверить статус и коммиты.
- **Workflow изолированной задачи:** В `agent-isolated-task-workflow.md` описан полный цикл: проверка/создание ветки → этапы с планом и подтверждением → pytest, ruff, architecture_linter, seed_db → ревью guardian → merge только по явной команде.
- **Текущий фокус:** В `current-focus.md` указана ветка `feature/ledger-ready-mvp`, отсылка к git-branch-policy и порядок работы (в т.ч. проверки и guardian).
- **Чек-лист перед «готово»:** В `workflow-orchestration.md` (раздел 1.7) есть architecture_linter и seed_db.
- **CI:** В `.github/workflows/backend-tests.yml` запускается `python -m app.scripts.architecture_linter`.
- **Ревью архитектуры:** Роль `architecture-guardian` в `.cursor/rules/architecture-guardian.mdc` и в `.cursor/rules/agents/architecture-guardian.mdc`.

---

## 3. Алгоритм твоих действий (чтобы не ломать архитектуру и держать контроль)

### 3.1 В начале сессии

1. Открыть **`docs/development-index.md`** — что в приоритете (Топ-5) и куда смотреть.
2. Если работаешь над конкретной задачей (например, Ledger-ready) — открыть **`docs/plan/current-focus.md`**: на какой ветке работать, что делать по шагам, какие проверки гнать.
3. Если нужно общее понимание «как вести разработку и целостность» — **`docs/plan/development-plan-and-integrity.md`**.

### 3.2 Перед тем как дать агенту изолированную задачу

1. Сформулировать задачу и (по желанию) имя ветки, например: `feature/ledger-ready-mvp`.
2. Сказать агенту следовать:
   - **`docs/plan/agent-isolated-task-workflow.md`**
   - правилу **`.cursor/rules/git-branch-policy.mdc`**
3. Если задача многоэтапная — дать ссылку на спецификацию (например, `docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`) и напомнить: этапы по порядку, после каждого этапа — проверки и @architecture-guardian.

### 3.3 Во время работы агента

1. Агент не должен коммитить в main/master и не должен мержить без твоей команды.
2. После каждого этапа — pytest, ruff, architecture_linter, seed_db; затем ревью по затронутым модулям (@architecture-guardian).
3. Мелкие замечания — агент правит сам; серьёзные — только после твоего «да».

### 3.4 Перед merge в main

1. Убедиться, что все этапы выполнены и все проверки зелёные.
2. Проверить отчёт ревью (architecture-guardian).
3. Явно дать команду: «мержи в main» / «одобряю слияние» (или выполнить merge сам).

### 3.5 После merge или смены приоритета

1. Обновить **`docs/plan/current-focus.md`**: на чём остановились, что делать дальше, статус этапов.
2. При закрытии задачи из Топ-5 или docs/tasks — обновить индекс и, при необходимости, PENDING_GAPS/RESOLVED_GAPS (по правилам из development-index).

### 3.6 Запреты (кратко)

- Не коммитить в main/master при изолированной задаче.
- Не мержить в main без явного одобрения.
- Не переходить к следующему этапу, пока не пройдены проверки и ревью по текущему.
- Не менять глоссарии без Lead Architect (см. OWNERSHIP.md).
- Не обновлять диаграммы/модель «после» кода — сначала схема (Schema First).

---

## 4. Связь документов (навигация)

```
docs/development-index.md          ← единая точка входа (открыть первым)
├── Топ-5, дорожная карта, роли
├── Быстрые ссылки → current-focus, plan, задачи
│
docs/plan/current-focus.md        ← «где остановились / что делать завтра»
├── Ветка для задачи, правило git-branch-policy
├── Порядок работы, этапы, ссылка на спецификацию
│
docs/plan/development-plan-and-integrity.md  ← план разработки и целостность
├── Как не метаться, как сохранять целостность
├── Таблица «Где что лежит»
│
docs/plan/agent-isolated-task-workflow.md     ← workflow изолированной задачи
├── Начало работы (ветка), этапы, проверки, ревью, merge
├── Ссылки: git-branch-policy.mdc, architecture-guardian, workflow-orchestration 1.7
│
.cursor/rules/git-branch-policy.mdc          ← правило для агента: ветки, не main, не merge
.cursor/rules/architecture-guardian.mdc      ← ревью архитектуры
docs/tasks/workflow-orchestration.md         ← Pre-Commit Checklist (1.7)
```

---

## 5. Замечание по техническому долгу

~~В `development-plan-and-integrity.md` указано: architecture linter пока отмечает нарушения в `accruals/api/contribution_types.py` и `cooperative_core/api/routes.py` (импорт из infrastructure). Это не отменяет соблюдение workflow: процесс и правила соблюдаются, но перед «всё зелёное» эти нарушения имеет смысл со временем исправить.~~

**Обновление 2026-03-05:** Все нарушения architecture linter устранены. API больше не импортирует infrastructure; проверка регистрации моделей учитывает импорт по модулям. Часть тестов (expenses, meters, land_plots и др.) по-прежнему падает из‑за абстрактных репозиториев — это отдельный технический долг проекта.

---

*Документ можно обновлять при изменении процесса или появлении новых правил.*
