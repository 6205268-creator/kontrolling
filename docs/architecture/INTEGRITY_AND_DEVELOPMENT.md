# Архитектурная целостность и процесс разработки

**Дата создания:** 2026-03-04  
**Владелец:** Lead Architect  
**Статус:** Действующий стандарт проекта

---

## 📋 Введение

Этот документ отвечает на критические вопросы о поддержании целостности системы при разработке, предотвращении регрессий и контроле за изменениями, вносимыми AI-агентами.

**Цель:** Обеспечить стабильную, предсказуемую разработку без «ломания» одних фич при добавлении других.

---

## 🔍 Анализ текущего состояния

### Что УЖЕ работает в проекте

| Механизм | Статус | Описание |
|----------|--------|----------|
| **Development Index** | ✅ Активен | `docs/development-index.md` — единая точка входа |
| **Правило индекса** | ✅ `alwaysApply: true` | `.cursor/rules/development-index-rule.mdc` |
| **Project Conventions** | ✅ `alwaysApply: true` | `.cursor/rules/project-conventions.mdc` |
| **Workflow Orchestration** | ✅ Активен | Планирование, верификация, уроки |
| **ADR процесс** | ✅ Зафиксирован | `docs/architecture/adr/README.md` |
| **Ownership** | ✅ Зафиксирован | `docs/architecture/OWNERSHIP.md` |
| **Schema First** | ✅ Правило | Диаграммы до кода |
| **Тесты** | ✅ 197 тестов | In-memory SQLite, CI в GitHub Actions |
| **Feature Workflow** | ✅ Зафиксирован | `docs/context-tree/feature-workflow-prompt.md` |
| **История фич** | ✅ 35 версионных файлов | `docs/context-tree/features/Fxx-v1-date.md` |

---

## ❌ Выявленные проблемы и риски

### Проблема 1: Нет «архитектурного надзора» для AI-агентов

**Симптом:**
> «Если какой-то агент будет отслеживать изменения, предложенные другими агентами... и принимать решения, корректны ли их изменения»

**Текущее состояние:**
- ✅ Есть `development-index-rule.mdc` с `alwaysApply: true`
- ✅ Есть `project-conventions.mdc` с `alwaysApply: true`
- ❌ **Нет автоматической проверки на соответствие архитектурным стандартам**
- ❌ **Нет агента-валидатора архитектурной целостности**

**Риск:** AI-агент может внести изменения, которые:
- Нарушают границы слоёв Clean Architecture
- Создают циклические зависимости между модулями
- Дублируют существующую функциональность
- Нарушают принцип «FinancialSubject как ядро»

---

### Проблема 2: Нет явного процесса code review для AI-изменений

**Симптом:**
> «Когда я начинаю делать очередную фичу, она ломает предыдущие две»

**Текущее состояние:**
- ✅ Тесты запускаются (`pytest`, 197 тестов)
- ✅ CI в GitHub Actions
- ❌ **Нет обязательного pre-commit review на архитектурные нарушения**
- ❌ **Нет «архитектурного чек-листа» для агентов**

**Риск:** Изменения проходят в код, если тесты зелёные, но нарушают архитектуру.

---

### Проблема 3: Глоссарии заполнены частично (3 из 10)

**Симптом:**
> «Противоречат ли изменения стандартам, заложенным заранее»

**Текущее состояние:**
- ✅ Политика зафиксирована (`OWNERSHIP.md`, `glossary/README.md`)
- ✅ Только Lead Architect может менять глоссарии
- ❌ **7 доменов без глоссариев** (cooperative, land, payments, expenses, meters, reporting, administration)

**Риск:** Разные агенты могут использовать разную терминологию для одних и тех же концепций.

---

## 🏗️ Архитектура целостности системы

### Уровень 1: Preventive (Предотвращение)

| Механизм | Файл | Статус | Описание |
|----------|------|--------|----------|
| **Development Index Rule** | `.cursor/rules/development-index-rule.mdc` | ✅ | Всегда читай индекс перед работой |
| **Project Conventions** | `.cursor/rules/project-conventions.mdc` | ✅ | SOLID, KISS, не придумывать требования |
| **Architecture Rules** | `.cursor/rules/architecture/architecture-rules.mdc` | ✅ | Mermaid, C4 naming, Schema First |
| **Workflow Orchestration** | `.cursor/rules/plan/workflow-orchestration.mdc` | ✅ | План → Реализация → Верификация → Уроки |

**Как работает:**
1. Агент открывает задачу → срабатывает `development-index-rule.mdc` → читает индекс
2. Перед кодом → срабатывает `architecture-rules.mdc` → проверяет диаграммы
3. Во время работы → срабатывает `workflow-orchestration.mdc` → план в `todo.md`
4. После работы → тесты + верификация → «утвердил бы staff engineer?»

---

### Уровень 2: Detective (Обнаружение)

| Механизм | Файл | Статус | Описание |
|----------|------|--------|----------|
| **Unit/API тесты** | `backend/tests/` | ✅ | 197 тестов, in-memory SQLite |
| **CI/CD** | `.github/workflows/backend-tests.yml` | ✅ | Запуск на каждый push |
| **Ruff linting** | `pyproject.toml` | ✅ | Line-length 100, target py311 |
| **История фич** | `docs/context-tree/features/Fxx-v1-date.md` | ✅ | 35 версионных файлов |

**Как работает:**
1. Агент внёс изменения → запустил `pytest` → все тесты зелёные
2. Push в репозиторий → GitHub Actions → тесты + линтеры
3. Если тесты красные → агент исправляет сам (правило 1.6 из workflow)

---

### Уровень 3: Corrective (Исправление)

| Механизм | Файл | Статус | Описание |
|----------|------|--------|----------|
| **Уроки (Lessons)** | `docs/tasks/lessons.md` | ⚠️ | Файл существует, но может быть пустым |
| **PENDING_GAPS** | `docs/history/PENDING_GAPS.md` | ✅ | 1 дыра (глоссарии, Low) |
| **RESOLVED_GAPS** | `docs/history/RESOLVED_GAPS.md` | ✅ | 9 закрытых дыр |
| **DECISIONS_LOG** | `docs/history/DECISIONS_LOG.md` | ✅ | 3 решения (DEC-001–DEC-003) |

**Как работает:**
1. Ошибка обнаружена → агент исправляет → записывает урок в `lessons.md`
2. Архитектурное нарушение → запись в `PENDING_GAPS` → исправление → `RESOLVED_GAPS`
3. Новое решение → `DECISIONS_LOG` + ADR

---

## 🛡️ Система защиты от регрессий

### Защита 1: Clean Architecture Module Boundaries

**Правило:**
```
{module_name}/
├── domain/           # Pure Python (без зависимостей)
├── application/      # Use Cases + DTOs (без фреймворков)
├── infrastructure/   # ORM, repositories (без API)
└── api/              # FastAPI routes (без infrastructure)
```

**Запрещено:**
- ❌ API layer импортирует из infrastructure
- ❌ application импортирует из infrastructure напрямую
- ❌ domain импортирует что-либо кроме стандартной библиотеки Python

**Как проверить:**
```bash
# Запустить перед коммитом
ruff check backend/app/modules/
```

---

### Защита 2: FinancialSubject как ядро

**Правило из `entities-minimal.md`:**
> Все финансовые операции (`Accrual`, `Payment`) работают **только** через `FinancialSubject`. Прямые связи с `LandPlot`, `Meter` запрещены.

**Проверка:**
```python
# ✅ ПРАВИЛЬНО:
accrual.financial_subject_id = fs.id
payment.financial_subject_id = fs.id

# ❌ НЕПРАВИЛЬНО:
accrual.land_plot_id = plot.id  # Запрещено!
payment.meter_id = meter.id     # Запрещено!
```

---

### Защита 3: Soft Delete для финансовых сущностей

**Правило:**
> Hard delete запрещён для Accrual, Payment, Expense. Использовать `status = archived|cancelled`.

**Проверка:**
```python
# ✅ ПРАВИЛЬНО:
accrual.status = "cancelled"
payment.status = "cancelled"

# ❌ НЕПРАВИЛЬНО:
db.delete(accrual)  # Запрещено!
session.delete(payment)  # Запрещено!
```

---

### Защита 4: Schema First

**Правило:**
> Диаграммы обновляются ДО изменений в коде.

**Процесс:**
1. Изменил `docs/data-model/schema-viewer.html` или `.mmd` файл
2. Закоммитил диаграмму
3. Только потом пишешь код

**Проверка перед коммитом:**
```bash
# Убедись, что диаграммы актуальны
git diff docs/data-model/
git diff docs/architecture/
```

---

## 🤖 Роль AI-агентов в поддержании целостности

### Агент 1: Development Index Reader (alwaysApply)

**Файл:** `.cursor/rules/development-index-rule.mdc`

**Обязанности:**
- Перед работой читает `docs/development-index.md`
- Смотрит «Топ-5» задач
- Проверяет приоритет источников при конфликте

---

### Агент 2: Architecture Guardian (предлагается добавить)

**Файл:** `.cursor/rules/architecture-guardian.mdc` (создать)

**Обязанности:**
- Проверяет изменения на нарушение границ слоёв
- Сверяет с ADR и глоссариями
- Блокирует коммиты с архитектурными нарушениями

**Чек-лист проверки:**
```markdown
## Архитектурный чек-лист

- [ ] Не нарушены границы модулей (domain → application → infrastructure → api)
- [ ] Нет циклических зависимостей между модулями
- [ ] FinancialSubject используется для всех начислений/платежей
- [ ] Нет hard delete для финансовых сущностей
- [ ] Диаграммы обновлены (Schema First)
- [ ] Терминология согласована с глоссариями
- [ ] Тесты покрывают изменения (минимум 1 тест на use case)
- [ ] ADR создан (если решение значимое)
```

---

### Агент 3: Test Verifier (встроен в workflow)

**Файл:** `.cursor/rules/plan/workflow-orchestration.mdc` (раздел 1.4)

**Обязанности:**
- Запускает `pytest` после изменений
- Проверяет покрытие тестами
- Сравнивает поведение до/после (diff behavior)

**Команда:**
```bash
cd backend
pytest                          # Все тесты
pytest tests/test_api/          # Только API тесты
pytest tests/test_models/       # Только модельные тесты
```

---

### Агент 4: Lessons Recorder (встроен в workflow)

**Файл:** `.cursor/rules/plan/workflow-orchestration.mdc` (раздел 1.3)

**Обязанности:**
- После исправления ошибок обновляет `docs/tasks/lessons.md`
- Создаёт паттерны для предотвращения повторения
- В начале сессии читает релевантные уроки

---

## 📋 Процесс разработки фичи (пошагово)

### Шаг 0: Подготовка (Pre-Work)

```markdown
1. Открыть `docs/development-index.md` → секция 4.2 (Топ-5)
2. Взять задачу из списка
3. Открыть `docs/project-implementation.md` → найти фичу
4. Загрузить контекст: `docs/context-tree/features/Fxx.md`
```

---

### Шаг 1: План (Plan Node)

```markdown
1. Создать план в `docs/tasks/todo.md` (checkable items)
2. Проверить архитектурные ограничения:
   - ADR: `docs/architecture/adr/README.md`
   - Глоссарии: `docs/architecture/glossary/`
   - Модель данных: `docs/data-model/schema-viewer.html`
3. Check-in: сообщить пользователю план
```

**Файл:** `docs/tasks/todo.md`

```markdown
## Фича Fxx: [Название]

### План

- [ ] Шаг 1: [Описание]
- [ ] Шаг 2: [Описание]
- [ ] Шаг 3: [Описание]

### Архитектурные ограничения

- ADR: [Ссылка]
- Глоссарий: [Ссылка]
- Модель данных: [Ссылка]

### Check-in

[Дата] — план утверждён пользователем
```

---

### Шаг 2: Реализация (Implementation)

```markdown
1. Следовать плану из todo.md
2. На каждом шаге — краткое резюме изменений
3. Писать тесты ДО или ВО ВРЕМЯ кода (TDD preferred)
4. Проверять границы слоёв (не импортировать запрещённое)
```

**Пример резюме:**
```markdown
### Шаг 1: Создание модели

**Изменения:**
- `backend/app/modules/accruals/infrastructure/models.py` — AccrualModel
- `backend/alembic/versions/0005_add_accrual.py` — миграция

**Проверки:**
- ✅ Нет импортов из API layer
- ✅ FinancialSubject используется
- ✅ Статусы: created, applied, cancelled
```

---

### Шаг 3: Верификация (Verification)

```markdown
1. Запустить тесты: `pytest tests/test_api/test_accruals.py`
2. Проверить покрытие: все use cases покрыты тестами
3. Запустить линтеры: `ruff check .`
4. Self-review: «Утвердил бы staff engineer?»
```

**Чек-лист верификации:**
```markdown
## Верификация

- [ ] Все тесты зелёные (`pytest`)
- [ ] Линтеры проходят (`ruff check .`, `ruff format --check .`)
- [ ] Нет предупреждений в консоли
- [ ] Диаграммы обновлены (если менялась модель)
- [ ] ADR создан (если решение значимое)
```

---

### Шаг 4: Фиксация (Documentation)

```markdown
1. Обновить `docs/project-implementation.md`:
   - Отметить шаги `[x]`
   - Добавить ✅ в заголовок
2. Создать версионный файл:
   - Скопировать `docs/context-tree/features/Fxx.md`
   - Переименовать: `Fxx-v1-YYYY-MM-DD.md`
   - Добавить блок «Выполнено»
3. Обновить `docs/history/RESOLVED_GAPS.md` (если закрывалась дыра)
```

---

### Шаг 5: Уроки (Lessons)

```markdown
1. Если были замечания → обновить `docs/tasks/lessons.md`
2. Создать паттерн: «Если X → делай Y, не делай Z»
3. В начале следующей сессии → прочитать релевантные уроки
```

**Файл:** `docs/tasks/lessons.md`

```markdown
## Урок: [Название]

**Контекст:** [Когда применимо]

**Паттерн:**
- Если [ситуация X] → делай [Y]
- Не делай [Z] (нарушает [правило])

**Пример:**
[Код или ссылка на коммит]
```

---

## 🚨 Контрольные точки (Gates)

### Gate 1: Перед началом работы

```markdown
## Check-in перед реализацией

- [ ] Development Index прочитан
- [ ] План в todo.md создан
- [ ] Архитектурные ограничения проверены
- [ ] Пользователь утвердил план
```

---

### Gate 2: Перед коммитом

```markdown
## Pre-commit проверка

- [ ] `pytest` — все тесты зелёные
- [ ] `ruff check .` — нет ошибок
- [ ] `ruff format --check .` — форматирование корректно
- [ ] Диаграммы обновлены (если менялась модель)
- [ ] ADR создан (если нужно)
```

---

### Gate 3: Перед пушем

```markdown
## Pre-push проверка

- [ ] CI в GitHub Actions пройдёт (локально проверено)
- [ ] `docs/project-implementation.md` обновлён
- [ ] Версионный файл создан (`Fxx-v1-date.md`)
- [ ] Lessons обновлены (если были замечания)
```

---

## 🔧 Инструменты для поддержания целостности

### Инструмент 1: Архитектурный линтер (предлагается)

**Создать скрипт:** `backend/app/scripts/architecture_linter.py`

```python
"""
Проверка архитектурных ограничений перед коммитом.

Запуск: python -m app.scripts.architecture_linter
"""

import ast
import sys
from pathlib import Path

FORBIDDEN_IMPORTS = {
    # API layer не должен импортировать из infrastructure
    ("api", "infrastructure"): "API layer cannot import from infrastructure",
    # Application не должен импортировать из infrastructure напрямую
    ("application", "infrastructure"): "Application layer cannot import from infrastructure",
}

def check_architecture():
    modules_path = Path("app/modules")
    violations = []
    
    for module_dir in modules_path.iterdir():
        if not module_dir.is_dir():
            continue
        
        # Проверка запрещённых импортов
        for layer in ["api", "application", "domain", "infrastructure"]:
            layer_path = module_dir / layer
            if not layer_path.exists():
                continue
            
            for py_file in layer_path.glob("**/*.py"):
                with open(py_file) as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        # Проверка запрещённых импортов
                        for forbidden, message in FORBIDDEN_IMPORTS.items():
                            if forbidden[0] == layer and forbidden[1] in node.module:
                                violations.append(f"{py_file}:{message}")
    
    if violations:
        print("❌ Архитектурные нарушения:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    
    print("✅ Архитектурных нарушений не обнаружено")
    sys.exit(0)

if __name__ == "__main__":
    check_architecture()
```

**Добавить в pre-commit:**
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: architecture-linter
      name: Architecture Linter
      entry: python -m app.scripts.architecture_linter
      language: system
      pass_filenames: false
```

---

### Инструмент 2: Чек-лист для AI-агентов (создать)

**Файл:** `.cursor/rules/architecture-checklist.mdc`

```markdown
---
description: Архитектурный чек-лист для проверки изменений
alwaysApply: false
---

# Архитектурный чек-лист

## Перед коммитом

### Границы слоёв

- [ ] API layer не импортирует из infrastructure
- [ ] Application layer не импортирует из infrastructure напрямую
- [ ] Domain layer не импортирует ничего кроме стандартной библиотеки

### Финансовое ядро

- [ ] Accrual использует FinancialSubject (не LandPlot напрямую)
- [ ] Payment использует FinancialSubject (не Meter напрямую)
- [ ] Нет hard delete для Accrual, Payment, Expense

### Модель данных

- [ ] Диаграммы обновлены (Schema First)
- [ ] Новые поля добавлены в `entities-minimal.md`
- [ ] Миграция Alembic создана

### Терминология

- [ ] Термины согласованы с глоссариями
- [ ] Если термин новый → предложено добавление в глоссарий

### Тесты

- [ ] Написан минимум 1 тест на use case
- [ ] Все тесты зелёные (`pytest`)
- [ ] Покрытие не уменьшилось

### Документация

- [ ] ADR создан (если решение значимое)
- [ ] `project-implementation.md` обновлён
- [ ] Версионный файл создан (`Fxx-v1-date.md`)
```

---

### Инструмент 3: Автоматический валидатор ADR (предлагается)

**Создать скрипт:** `backend/scripts/adr_validator.py`

```python
"""
Проверка: создан ли ADR для значимых изменений.

Запуск: python -m app.scripts.adr_validator --check
"""

import sys
from pathlib import Path

ADR_PATH = Path("docs/architecture/adr")
SIGNIFICANT_CHANGES = [
    "новая модель",
    "новый модуль",
    "интеграция",
    "изменение стека",
    "безопасность",
]

def check_adr_required(changes_description: str) -> bool:
    for keyword in SIGNIFICANT_CHANGES:
        if keyword in changes_description.lower():
            return True
    return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Проверка: есть ли ADR для последних изменений
        # (интеграция с git diff)
        print("ADR Validator: проверка...")
        # TODO: реализовать интеграцию с git
    else:
        print("Использование: adr_validator --check")

if __name__ == "__main__":
    main()
```

---

## 📊 Метрики целостности

### Метрика 1: Architectural Debt Index

**Формула:**
```
ADI = (PENDING_GAPS count × 1) + (ADR missing count × 3) + (Glossary gaps × 0.5)
```

**Текущее значение:**
- PENDING_GAPS: 1 (глоссарии, Low)
- ADR missing: 0 (все значимые решения задокументированы)
- Glossary gaps: 7 (cooperative, land, payments, expenses, meters, reporting, administration)

```
ADI = (1 × 1) + (0 × 3) + (7 × 0.5) = 1 + 0 + 3.5 = 4.5
```

**Цель:** ADI < 3

---

### Метрика 2: Regression Rate

**Формула:**
```
RR = (Regression bugs count) / (Features shipped count) × 100%
```

**Текущее значение:**
- Regression bugs: 0 (нет зафиксированных регрессий)
- Features shipped: 35

```
RR = 0 / 35 × 100% = 0%
```

**Цель:** RR < 5%

---

### Метрика 3: Test Coverage Trend

**Формула:**
```
TCT = (Current test count) - (Previous test count)
```

**Текущее значение:**
- Current: 197 тестов
- Previous: отслеживать по истории

**Цель:** TCT > 0 (покрытие растёт с каждой фичей)

---

## 🎯 Рекомендации по дальнейшей работе

### Приоритет 1: Создать Architecture Guardian

**Задача:**
- Создать `.cursor/rules/architecture-guardian.mdc`
- Добавить чек-лист из 8 пунктов (границы, FinancialSubject, soft delete, диаграммы, глоссарии, тесты, ADR)
- Установить `alwaysApply: false` с вызовом через `@architecture-guardian`

**Срок:** Следующая сессия

---

### Приоритет 2: Заполнить глоссарии

**Задача:**
- Заполнить 7 недостающих глоссариев (cooperative, land, payments, expenses, meters, reporting, administration)
- Владелец: Lead Architect (только он может менять глоссарии)

**Срок:** 1-2 недели

---

### Приоритет 3: Автоматизировать архитектурный линтинг

**Задача:**
- Создать `backend/app/scripts/architecture_linter.py`
- Добавить в pre-commit hook
- Интегрировать в CI (GitHub Actions)

**Срок:** 1 неделя

---

### Приоритет 4: Расширить E2E тесты

**Задача:**
- Добавить E2E тесты на критические сценарии:
  - Создание начисления → применение → отмена
  - Регистрация платежа → отмена → перерасчёт баланса
  - Массовое начисление по участкам
- Использовать Playwright (уже настроен)

**Срок:** 2 недели

---

### Приоритет 5: Создать Dashboard целостности

**Задача:**
- Страница `docs/integrity-dashboard.html`
- Метрики в реальном времени:
  - ADI (Architectural Debt Index)
  - RR (Regression Rate)
  - TCT (Test Coverage Trend)
  - PENDING_GAPS count
  - ADR count
- Обновление при каждом коммите

**Срок:** 1 неделя

---

## 📝 Итоговый чек-лист для разработчика

### Перед началом работы

```markdown
- [ ] Открыл `docs/development-index.md` → прочитал Топ-5
- [ ] Взял задачу из списка приоритетов
- [ ] Создал план в `docs/tasks/todo.md`
- [ ] Проверил ADR и глоссарии
- [ ] Утвердил план с пользователем (check-in)
```

---

### Во время работы

```markdown
- [ ] Следую плану (todo.md)
- [ ] Пишу тесты ДО или ВО ВРЕМЯ кода
- [ ] Проверяю границы слоёв (не импортирую запрещённое)
- [ ] Использую FinancialSubject для начислений/платежей
- [ ] Не делаю hard delete для финансовых сущностей
- [ ] Даю краткое резюме на каждом шаге
```

---

### Перед коммитом

```markdown
- [ ] `pytest` — все тесты зелёные
- [ ] `ruff check .` — нет ошибок
- [ ] `ruff format --check .` — форматирование ОК
- [ ] Диаграммы обновлены (Schema First)
- [ ] ADR создан (если решение значимое)
- [ ] Архитектурный чек-лист пройден
```

---

### После коммита

```markdown
- [ ] Обновил `docs/project-implementation.md` (шаги [x], ✅)
- [ ] Создал версионный файл (`Fxx-v1-date.md`)
- [ ] Обновил `docs/tasks/lessons.md` (если были замечания)
- [ ] Проверил CI в GitHub Actions (зелёный)
```

---

## 🔗 Ссылки

| Документ | Путь |
|----------|------|
| Development Index | [`docs/development-index.md`](docs/development-index.md) |
| Project Conventions | [`.cursor/rules/project-conventions.mdc`](.cursor/rules/project-conventions.mdc) |
| Workflow Orchestration | [`.cursor/rules/plan/workflow-orchestration.mdc`](.cursor/rules/plan/workflow-orchestration.mdc) |
| Architecture Rules | [`.cursor/rules/architecture/architecture-rules.mdc`](.cursor/rules/architecture/architecture-rules.mdc) |
| ADR Index | [`docs/architecture/adr/README.md`](docs/architecture/adr/README.md) |
| Ownership | [`docs/architecture/OWNERSHIP.md`](docs/architecture/OWNERSHIP.md) |
| Feature Workflow | [`docs/context-tree/feature-workflow-prompt.md`](docs/context-tree/feature-workflow-prompt.md) |

---

*Документ создан: 2026-03-04*  
*Владелец: Lead Architect*  
*Статус: Действующий стандарт*
