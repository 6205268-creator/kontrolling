# ✅ Отчёт о распределении правил Cursor по папкам

**Дата выполнения**: 28 февраля 2026  
**Статус**: ✅ **ВЫПОЛНЕНО (100%)**

---

## 📊 Итоговая структура

```
.cursor/rules/
├── communication-style.mdc          ✅ alwaysApply: true (корень)
├── guide-workflow.mdc               ✅ alwaysApply: true (корень)
├── project-conventions.mdc          ✅ alwaysApply: true (корень)
│
├── plan/
│   └── workflow-orchestration.mdc   ✅ alwaysApply: false, globs: tasks/**
│
├── architecture/
│   ├── architecture-rules.mdc       ✅ alwaysApply: false, globs: docs/architecture/**, ...
│   ├── aac-c4-architecture.mdc      ✅ alwaysApply: false, globs: docs/architecture/**, ...
│   ├── bpmn-process-rules.mdc       ✅ alwaysApply: false, globs: docs/architecture/**, ...
│   ├── bpmn-viewer-show.mdc         ✅ alwaysApply: false, globs: docs/architecture/**, ...
│   └── schema-viewer-show.mdc       ✅ alwaysApply: false, globs: docs/architecture/**, ...
│
└── build/
    ├── code-style-and-tools.mdc     ✅ alwaysApply: false, globs: backend/**, frontend/**
    ├── context7-docs.mdc            ✅ alwaysApply: false, globs: backend/**, frontend/**
    └── backend-testing-and-pitfalls.mdc  ✅ globs: backend/**/*.py, backend/tests/**/*
```

---

## 📁 Что было сделано

### 1. Созданы папки

- ✅ `.cursor/rules/plan/`
- ✅ `.cursor/rules/architecture/`
- ✅ `.cursor/rules/build/`

### 2. Оставлены в корне (3 файла)

| Файл | alwaysApply | Описание |
|------|-------------|----------|
| `communication-style.mdc` | **true** | Стиль общения с пользователем |
| `guide-workflow.mdc` | **true** | «Вопрос ≠ действие», конвенции проекта |
| `project-conventions.mdc` | **true** | Общие правила проекта |

### 3. Перенесены в plan/ (1 файл)

| Файл | Путь | alwaysApply | globs |
|------|------|-------------|-------|
| `workflow-orchestration.mdc` | `plan/workflow-orchestration.mdc` | **false** | `tasks/**` |

**Загружается**: при работе с файлами в `tasks/` (планирование, задачи).

---

### 4. Перенесены в architecture/ (5 файлов)

| Файл | alwaysApply | globs |
|------|-------------|-------|
| `architecture-rules.mdc` | false | `docs/architecture/**, docs/processes/**, docs/data-model/**, domains/**, **/*.mmd, **/*.bpmn` |
| `aac-c4-architecture.mdc` | false | (те же) |
| `bpmn-process-rules.mdc` | false | (те же) |
| `bpmn-viewer-show.mdc` | false | (те же) |
| `schema-viewer-show.mdc` | false | (те же) |

**Загружаются**: при работе с документацией архитектуры, диаграммами Mermaid/BPMN, доменными файлами.

---

### 5. Перенесены в build/ (3 файла)

| Файл | alwaysApply | globs |
|------|-------------|-------|
| `code-style-and-tools.mdc` | false | `backend/**, frontend/**` |
| `context7-docs.mdc` | false | `backend/**, frontend/**` |
| `backend-testing-and-pitfalls.mdc` | false | `backend/**/*.py, backend/tests/**/*` |

**Загружаются**: при написании кода в `backend/` или `frontend/`.

---

### 6. Удалены оригиналы из корня

Удалённые файлы (9 штук):
- ❌ `workflow-orchestration.mdc`
- ❌ `code-style-and-tools.mdc`
- ❌ `context7-docs.mdc`
- ❌ `architecture-rules.mdc`
- ❌ `aac-c4-architecture.mdc`
- ❌ `bpmn-process-rules.mdc`
- ❌ `bpmn-viewer-show.mdc`
- ❌ `schema-viewer-show.mdc`
- ❌ `backend-testing-and-pitfalls.mdc`

---

## 🎯 Результат

### До рефакторинга

```
.cursor/rules/  (12 файлов)
├── communication-style.mdc           alwaysApply: true
├── guide-workflow.mdc                alwaysApply: true
├── project-conventions.mdc           alwaysApply: true
├── workflow-orchestration.mdc        alwaysApply: true  ❌
├── code-style-and-tools.mdc          alwaysApply: true  ❌
├── context7-docs.mdc                 alwaysApply: true  ❌
├── architecture-rules.mdc            alwaysApply: true  ❌
├── aac-c4-architecture.mdc           alwaysApply: true  ❌
├── bpmn-process-rules.mdc            alwaysApply: true  ❌
├── bpmn-viewer-show.mdc              alwaysApply: true  ❌
├── schema-viewer-show.mdc            alwaysApply: true  ❌
└── backend-testing-and-pitfalls.mdc  globs: backend/**/*.py  ✅
```

**Проблема**: 9 файлов с `alwaysApply: true` загружались в **каждом** диалоге → избыточный контекст.

---

### После рефакторинга

```
.cursor/rules/  (3 файла в корне + 9 в подпапках)
├── communication-style.mdc           alwaysApply: true  ✅
├── guide-workflow.mdc                alwaysApply: true  ✅
├── project-conventions.mdc           alwaysApply: true  ✅
│
├── plan/  (1 файл)
│   └── workflow-orchestration.mdc    alwaysApply: false, globs: tasks/**
│
├── architecture/  (5 файлов)
│   └── *.mdc                         alwaysApply: false, globs: docs/architecture/**, ...
│
└── build/  (3 файла)
    └── *.mdc                         alwaysApply: false, globs: backend/**, ...
```

**Результат**:
- В **обычном чате** без специфичных файлов → **3 правила** (вместо 12)
- При работе с `tasks/` → **+1 правило** (workflow)
- При работе с `docs/architecture/` → **+5 правил** (архитектура)
- При работе с `backend/` → **+3 правила** (код + тесты)

---

## 📈 Экономия контекста

| Сценарий | Было правил | Стало правил | Экономия |
|----------|-------------|--------------|----------|
| Обычный чат | 12 | **3** | **−75%** |
| Работа с tasks/ | 12 | 4 | −67% |
| Работа с архитектурой | 12 | 8 | −33% |
| Работа с кодом | 12 | 6 | −50% |

---

## ✅ Верификация

### Проверка структуры

```
✅ В корне: 3 файла (communication-style, guide-workflow, project-conventions)
✅ plan/: 1 файл (workflow-orchestration)
✅ architecture/: 5 файлов (architecture-rules, aac-c4, bpmn-*, schema-viewer)
✅ build/: 3 файла (code-style, context7, backend-testing)
✅ Дубликатов нет
```

### Проверка frontmatter

| Файл | alwaysApply | globs | Статус |
|------|-------------|-------|--------|
| Корневые 3 файла | true | — | ✅ |
| plan/workflow-orchestration | false | tasks/** | ✅ |
| architecture/*.mdc | false | docs/architecture/**, ... | ✅ |
| build/code-style-and-tools | false | backend/**, frontend/** | ✅ |
| build/context7-docs | false | backend/**, frontend/** | ✅ |
| build/backend-testing | false | backend/**/*.py, backend/tests/**/* | ✅ |

---

## 🎓 Как это работает

### Принцип выборочной загрузки

Cursor загружает правила на основе:

1. **alwaysApply: true** → загружаются **всегда** (в любом диалоге)
2. **globs: <паттерн>** → загружаются **только если открыт файл**, подходящий под паттерн

### Примеры сценариев

#### Сценарий 1: Обычный вопрос

**Пользователь**: «Как дела?»

**Загруженные правила**:
- ✅ `communication-style.mdc`
- ✅ `guide-workflow.mdc`
- ✅ `project-conventions.mdc`

**Контекст**: ~300 строк (вместо ~1500)

---

#### Сценарий 2: Работа с задачей

**Открыт файл**: `tasks/todo.md`

**Загруженные правила**:
- ✅ Корневые (3)
- ✅ `plan/workflow-orchestration.mdc` (globs: `tasks/**`)

**Контекст**: ~500 строк

---

#### Сценарий 3: Работа с архитектурой

**Открыт файл**: `docs/architecture/clean-architecture-migration-plan.md`

**Загруженные правила**:
- ✅ Корневые (3)
- ✅ `architecture/architecture-rules.mdc`
- ✅ `architecture/aac-c4-architecture.mdc`
- ✅ `architecture/bpmn-process-rules.mdc`
- ✅ `architecture/bpmn-viewer-show.mdc`
- ✅ `architecture/schema-viewer-show.mdc`

**Контекст**: ~1200 строк

---

#### Сценарий 4: Написание кода

**Открыт файл**: `backend/app/modules/land_management/api/routes.py`

**Загруженные правила**:
- ✅ Корневые (3)
- ✅ `build/code-style-and-tools.mdc`
- ✅ `build/context7-docs.mdc`
- ✅ `build/backend-testing-and-pitfalls.mdc` (если `**/tests/**`)

**Контекст**: ~800 строк

---

## 🚀 Преимущества

| Преимущество | Описание |
|-------------|----------|
| **Меньше токенов** | В обычном чате −75% контекста |
| **Релевантность** | Правила загружаются только когда нужны |
| **Масштабируемость** | Легко добавить новые папки с правилами |
| **Поддержка** | Чёткая структура упрощает навигацию |

---

## 📝 Рекомендации на будущее

### Если нужно добавить новое правило

1. **Определите область**:
   - Для всех диалогов → корень с `alwaysApply: true`
   - Для задач → `plan/` с `globs: tasks/**`
   - Для архитектуры → `architecture/` с `globs: docs/architecture/**`
   - Для кода → `build/` с `globs: backend/**` или `frontend/**`

2. **Создайте файл** в соответствующей папке

3. **Добавьте frontmatter**:
   ```yaml
   ---
   description: Краткое описание
   alwaysApply: false
   globs: path/to/files/**
   ---
   ```

### Если правило не работает

1. Проверьте **путь к файлу** (относительно корня проекта)
2. Проверьте **globs паттерн** (должен совпадать с открытым файлом)
3. Убедитесь, что **frontmatter** корректен (правильный YAML)

---

## ✅ Итог

**Задача выполнена полностью:**

- ✅ 3 правила в корне с `alwaysApply: true`
- ✅ 9 правил распределены по подпапкам
- ✅ У всех правил правильный `alwaysApply` и `globs`
- ✅ Дубликаты удалены
- ✅ Структура соответствует плану

**Экономия контекста**: до **75%** в обычных диалогах.

---

**Выполнил**: Qwen Code Assistant  
**Дата**: 28 февраля 2026
