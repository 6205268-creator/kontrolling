# Архитектура документооборота проекта КОНТРОЛЛИНГ

**Дата:** 2026-03-09  
**Роль:** Архитектор документооборота и аналитик проектной информации  
**Назначение:** Итог анализа разросшейся системы документов — дублирование, противоречия, иерархия, точки входа, связь с GitHub и единая архитектура управления информацией.

---

## 1. Таблица файлов: назначение, дублирование, статус

Ниже — ключевые документы проекта с уровнем дублирования и рекомендацией (оставить / удалить / объединить / архивировать).

| Файл | Назначение | Дублирование | Статус |
|------|------------|---------------|--------|
| **Корень и точка входа** |
| `docs/development-index.md` | Единая точка входа: Топ-5, дорожная карта, ссылки на всё | Нет (источник) | **Оставить** |
| `AGENTS.md` | Quick Start для агентов, стек, Pitfalls, ссылка на индекс | Частично дублирует стек с README/QWEN; ссылки на индекс — усиление, не дубль | **Оставить** |
| `README.md` | Визитка репозитория, стек, структура, ссылка на индекс | Краткий дубль стека/структуры с AGENTS.md | **Оставить** (разная аудитория) |
| `QWEN.md` | Контекст для Qwen/других ассистентов: стек, workflow, индекс | Существенное дублирование с AGENTS.md по стеку и workflow | **Объединить** или оставить как тонкую обёртку со ссылкой на AGENTS.md + индекс |
| **План и дорожная карта** |
| `docs/project-implementation.md` | Дорожная карта: 35 фич, шаги, проверки | Единственный источник фич | **Оставить** |
| `docs/project-design.md` | Дизайн системы: цели, стек, модель данных, роли | Единственный полный дизайн | **Оставить** |
| `docs/product-context.md` | Продуктовый контекст: проблемы СТ, решение, цели | Уникальный контент | **Оставить** |
| **План разработки и целостность** |
| `docs/plan/development-plan-and-integrity.md` | Как не «метаться», целостность, где что лежит | Частично пересекается с INTEGRITY_AND_DEVELOPMENT | **Оставить** (короткий, оперативный) |
| `docs/plan/current-focus.md` | Где остановились, что делать завтра, ветка, этапы | Уникальный контекст сессии | **Оставить** |
| `docs/plan/CONCLUSION-SINGLE-ENTRY-AND-BRANCH-WORKFLOW.md` | Вывод: единая точка входа и workflow веток соблюдаются | Фиксация проверки; дублирует описание процесса из development-plan-and-integrity | **Оставить** (артефакт верификации) |
| `docs/plan/agent-isolated-task-workflow.md` | Workflow изолированной задачи (ветка → этапы → ревью → merge) | Уникальный процесс | **Оставить** |
| `docs/plan/single_development_index_and_roadmap.plan.md` | План консолидации (этапы 1–6), уже выполнен | Исторический план; индекс создан | **Архивировать** в `docs/archive/plan-consolidation-2026-03/` |
| `docs/plan/agent-branch-workflow-implementation-plan.md` | План внедрения workflow веток | Выполнен (есть agent-isolated-task-workflow, git-branch-policy) | **Архивировать** |
| `docs/plan/implementation-report-agent-branch-workflow.md` | Отчёт о внедрении workflow | Артефакт | **Архивировать** |
| `docs/plan/agent-branch-workflow-supplements.md` | Дополнения к workflow | Уточнения | **Оставить** или объединить в agent-isolated-task-workflow |
| `docs/plan/financial-architecture-analysis.md` | Анализ финансовой архитектуры (Ledger-ready) | Уникальный анализ | **Оставить** |
| **Краткие описания для агентов** |
| `docs/PROJECT_BRIEF_FOR_AGENTS.md` | Краткий бриф: что за проект, стержень, куда смотреть | Дублирует «стержень» и ссылки из индекса/AGENTS | **Оставить** (короткий онбординг; можно сократить до 1 страницы со ссылками) |
| **Архитектура и целостность** |
| `docs/architecture/INTEGRITY_AND_DEVELOPMENT.md` | Длинный документ: анализ целостности, проблемы, чек-листы, guardian | Значительное пересечение с development-plan-and-integrity по процессу и целостности | **Объединить**: выжимку «как сохранять целостность» и таблицу «где что» оставить в development-plan-and-integrity; детальные чек-листы и описание guardian — в INTEGRITY или в .cursor/rules | **Или оставить** как расширенный справочник, но в индексе явно указать: «кратко — development-plan-and-integrity, подробно — INTEGRITY_AND_DEVELOPMENT» |
| `docs/architecture/system-patterns.md` | Clean Architecture, модули, границы | Единственный источник паттернов | **Оставить** |
| `docs/architecture/adr/README.md` | Индекс и процесс ADR | Единственный | **Оставить** |
| `docs/architecture/OWNERSHIP.md` | Кто что может менять (глоссарии и т.д.) | Единственный | **Оставить** |
| `docs/architecture/environment-policy.md` | Политика окружений и переменных | Единственный | **Оставить** |
| **История и дыры** |
| `docs/history/PENDING_GAPS.md` | Открытые дыры | Единственный источник | **Оставить** |
| `docs/history/RESOLVED_GAPS.md` | Закрытые дыры | Единственный источник | **Оставить** |
| `docs/history/DECISIONS_LOG.md` | Лог решений DEC-001, DEC-002, DEC-003 | Единственный | **Оставить** |
| `docs/history/ANALYSIS_LOG.md` | Лог анализов | По назначению | **Оставить** |
| **Задания и процесс** |
| `docs/tasks/workflow-orchestration.md` | Оркестрация workflow, Pre-Commit Checklist | Уникальный | **Оставить** |
| `docs/tasks/todo.md` | Scratch-pad текущей задачи | По назначению | **Оставить** |
| `docs/tasks/lessons.md` | Уроки | По назначению | **Оставить** |
| `docs/tasks/e2e-setup.md` | E2E настройка | Уникальный | **Оставить** |
| `docs/tasks/TASK_*.md` | Задания по командам (выполнены) | Архив заданий | **Оставить** |
| `docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md` | Спека Ledger-ready MVP | Уникальный | **Оставить** |
| **Модель данных и контекст фич** |
| `docs/data-model/entities-minimal.md` | Минимальный набор сущностей | Единственный | **Оставить** |
| `docs/data-model/conceptual-model-prompt.md` | Промпт концептуальной модели | Единственный | **Оставить** |
| `docs/data-model/schema-viewer.html` | Интерактивная схема | Единственный | **Оставить** |
| `docs/context-tree/feature-workflow-prompt.md` | Workflow выполнения фичи | Уникальный | **Оставить** |
| `docs/context-tree/features/Fxx.md`, `Fxx-vN-date.md` | Пакеты контекста по фичам | По фичам | **Оставить** |
| `docs/feature-context-plan.md` | План дерева контекста фич | Описание подхода; реализовано (F01–F35) | **Оставить** (справочник) |
| **Декомпозиция и настройка** |
| `docs/decomposition.md` | Декомпозиция модулей, порядок разработки, **модель Payment/Accrual через land_plot_id** | **Противоречит** текущей модели (FinancialSubject) и коду | **Пометить устаревшим** или обновить под FinancialSubject; иначе — в архив с пометкой «устарело» |
| `docs/one-project-setup.md` | Один способ запуска (Docker + npm run dev) | Дублирует раздел запуска из AGENTS.md/README | **Оставить** (короткий, фокус на «один способ») |
| `docs/repository-sync-guide.md` | Руководство по синхронизации с репозиторием (git pull/push) | Уникальный, для владельца проекта | **Оставить** |
| `docs/ПАМЯТКА_ВЕРСИОНИРОВАНИЕ.md` | Памятка по версионированию (что говорить агенту) | Частично дублирует repository-sync-guide и git-branch-policy | **Оставить** (упрощённый язык для владельца) |
| **Рабочие и выполненные планы** |
| `docs/development-index-work.md` | Рабочий документ создания индекса; статус «завершено» | Черновик; индекс уже создан | **Архивировать** или удалить |
| **Деплой и обзоры** |
| `DEPLOY.md` | Инструкция деплоя (Docker и т.д.) | Дублирует часть AGENTS.md по Docker | **Оставить** (единое место для деплоя) |
| `docs/review-report.md` | Отчёт ревью (197 тестов, ruff) | Артефакт качества | **Оставить** |
| **Архив и исходники** |
| `docs/archive/*` | Старые версии (v0-python, v1-1c) | Архив | **Оставить** |
| `docs/source-material/*` | Исходные материалы (бизнес-логика СТ) | Справочник | **Оставить** |
| **Внешние системы** |
| `.qwen/skills/*` | Навыки Qwen | Вне docs, но проектная информация | Не трогать в рамках консолидации docs |
| `obsidian/*` | Заметки Obsidian | Внешний инструмент | Не трогать |

---

## 2. Карта противоречий

### 2.1 Критическое противоречие: модель данных (Payment / Accrual)

| Документ | Утверждение | Статус |
|----------|-------------|--------|
| `docs/decomposition.md` | Payment и Accrual привязаны к **участку** (`land_plot_id`); платёж/начисление — по участку. | **Устарело** |
| `docs/project-design.md`, `docs/project-implementation.md`, код, ADR | Все финансовые операции идут **только через FinancialSubject**. Прямых связей Accrual/Payment с LandPlot нет. | **Актуально** |

**Рекомендация:** В `decomposition.md` добавить в начало предупреждение: «Документ частично устарел: модель финансов приведена к FinancialSubject (см. project-design.md и project-implementation.md). Ниже — историческая декомпозиция модулей.» Либо перенести `decomposition.md` в `docs/archive/` с пометкой в имени (например `decomposition-deprecated-landplot-finance.md`).

### 2.2 Другие выявленные расхождения

- **Нет конфликтов по «единой точке входа»:** Все документы согласованы: точка входа — `docs/development-index.md`, Топ-5 и правила обновления там же.
- **Стек и структура:** AGENTS.md, README, QWEN.md, project-design — везде FastAPI + Vue 3 + PostgreSQL; расхождений нет.
- **Количество тестов:** В индексе и отчётах — 197; в плане single_development_index ранее было 192 — исправлено по факту.

---

## 3. Иерархия документов (главная дорожная карта на вершине)

```
Уровень 0 — Точка входа (одна)
└── docs/development-index.md     ← ГЛАВНАЯ ДОРОЖНАЯ КАРТА НАВИГАЦИИ (Топ-5, карта источников)

Уровень 1 — Дорожная карта и дизайн (source of truth по плану и архитектуре)
├── docs/project-implementation.md   ← Дорожная карта фич (35 фич, единственный источник)
├── docs/project-design.md           ← Дизайн системы (цели, стек, модель, роли)
└── docs/product-context.md          ← Продуктовый контекст (проблемы СТ, решение)

Уровень 2 — Процесс и контекст сессии
├── docs/plan/current-focus.md              ← Где остановились, что делать завтра
├── docs/plan/development-plan-and-integrity.md  ← Как вести разработку, целостность
├── docs/plan/agent-isolated-task-workflow.md    ← Workflow изолированной задачи
└── docs/tasks/workflow-orchestration.md        ← Оркестрация, Pre-Commit

Уровень 3 — Специализированные источники правды
├── docs/data-model/                  ← Модель данных (entities-minimal, schema-viewer)
├── docs/architecture/adr/            ← Архитектурные решения
├── docs/architecture/glossary/        ← Глоссарии (Lead Architect)
├── docs/architecture/system-patterns.md
├── docs/architecture/environment-policy.md
├── docs/architecture/OWNERSHIP.md
├── docs/history/PENDING_GAPS.md      ← Открытые дыры
├── docs/history/RESOLVED_GAPS.md     ← Закрытые дыры
├── docs/history/DECISIONS_LOG.md     ← Лог решений
└── docs/tasks/                       ← Задания (TASK_*, спецификации)

Уровень 4 — Вспомогательные и производные
├── docs/context-tree/features/       ← Пакеты контекста по фичам
├── docs/context-tree/feature-workflow-prompt.md
├── docs/PROJECT_BRIEF_FOR_AGENTS.md
├── docs/plan/CONCLUSION-SINGLE-ENTRY-AND-BRANCH-WORKFLOW.md
├── docs/architecture/INTEGRITY_AND_DEVELOPMENT.md  ← Подробный справочник по целостности
├── docs/repository-sync-guide.md
├── docs/one-project-setup.md
├── docs/ПАМЯТКА_ВЕРСИОНИРОВАНИЕ.md
└── DEPLOY.md

Уровень 5 — Архив и исходные материалы
├── docs/archive/                    ← Устаревшие версии документов и планов
└── docs/source-material/             ← Исходные материалы по предметной области
```

**Главная дорожная карта проекта в смысле «что делать»:** комбинация **`docs/development-index.md`** (Топ-5 + навигация) и **`docs/project-implementation.md`** (полный список фич и статусы). Индекс — вершина навигации; реализация — единственный источник правды по фичам.

---

## 4. План консолидации документов

### 4.1 Объединить

| Действие | Источники | Итоговый документ |
|----------|-----------|---------------------|
| Не объединять в один файл, а явно развести роли | `development-plan-and-integrity.md` (кратко) и `INTEGRITY_AND_DEVELOPMENT.md` (подробно) | В `development-index.md` в секции «Целостность» добавить строку: «Кратко: development-plan-and-integrity.md; подробный справочник: INTEGRITY_AND_DEVELOPMENT.md». |
| Опционально | QWEN.md и AGENTS.md | Оставить оба; в QWEN.md в начале указать: «Полный контекст: AGENTS.md; единая точка входа: docs/development-index.md». |

### 4.2 Архивировать

| Файл | Куда |
|------|------|
| `docs/plan/single_development_index_and_roadmap.plan.md` | `docs/archive/plan-consolidation-2026-03/` (создать папку) |
| `docs/plan/agent-branch-workflow-implementation-plan.md` | `docs/archive/plan-consolidation-2026-03/` |
| `docs/plan/implementation-report-agent-branch-workflow.md` | `docs/archive/plan-consolidation-2026-03/` |
| `docs/development-index-work.md` | `docs/archive/plan-consolidation-2026-03/` |

### 4.3 Пометить устаревшим или обновить

| Файл | Действие |
|------|----------|
| `docs/decomposition.md` | В начало файла добавить блок: «⚠️ Частично устарело: привязка платежей и начислений к участку (land_plot_id) заменена на модель через FinancialSubject. Актуальная модель: project-design.md, project-implementation.md.» Либо перенести в `docs/archive/` с именем, указывающим на устаревание. |

### 4.4 Не удалять как избыточные

Перечисленные в таблице выше документы со статусом «Оставить» выполняют разные роли (точка входа, процесс, контекст сессии, архив заданий). Удалять их как «избыточные» не рекомендуется; достаточно явной иерархии и ссылок из индекса.

---

## 5. Единая система хранения информации и интеграция с GitHub

### 5.1 Где что хранится (схема)

| Данные | Где хранятся |
|--------|-------------------------------|
| Что делать сейчас (приоритеты) | `docs/development-index.md` → секция Топ-5 |
| Дорожная карта фич (все 35) | `docs/project-implementation.md` |
| Где остановились / что завтра | `docs/plan/current-focus.md` |
| Процесс разработки и целостность | `docs/plan/development-plan-and-integrity.md` |
| Workflow веток и изолированных задач | `docs/plan/agent-isolated-task-workflow.md`, `.cursor/rules/git-branch-policy.mdc` |
| Дизайн системы | `docs/project-design.md` |
| Модель данных | `docs/data-model/` (entities-minimal, schema-viewer, conceptual-model-prompt) |
| Архитектурные решения | `docs/architecture/adr/` (README + нумерованные ADR) |
| Глоссарии по доменам | `docs/architecture/glossary/` |
| Открытые/закрытые дыры | `docs/history/PENDING_GAPS.md`, `docs/history/RESOLVED_GAPS.md` |
| Лог решений (DEC-xxx) | `docs/history/DECISIONS_LOG.md` |
| Задания по командам и спецификации | `docs/tasks/` (TASK_*.md, IMPLEMENTATION_SPEC_*.md, workflow-orchestration, todo, lessons, e2e-setup) |
| Контекст по фичам | `docs/context-tree/features/` (Fxx.md, Fxx-vN-date.md) |
| Правила для агентов | `.cursor/rules/` (development-index-rule, git-branch-policy, architecture-guardian, agents/*) |
| Инструкции для людей (деплой, синхронизация, версионирование) | `DEPLOY.md`, `docs/repository-sync-guide.md`, `docs/ПАМЯТКА_ВЕРСИОНИРОВАНИЕ.md` |
| Исходные материалы и архив | `docs/source-material/`, `docs/archive/` |

### 5.2 Связь с GitHub

- **Версионирование документации:** Всё в `docs/`, корневые `AGENTS.md`, `README.md`, `QWEN.md`, `DEPLOY.md` хранятся в Git. История изменений — `git log` по путям.
- **Семантическая история:** Принятые решения и закрытые дыры фиксируются в `DECISIONS_LOG.md`, `RESOLVED_GAPS.md`, ADR — это дополняет git log и даёт «почему» и «что закрыто».
- **Почему информация может быть разрознена:** (1) Несколько точек обновления (индекс, implementation, PENDING_GAPS, current-focus) без единого триггера «обнови всё». (2) Выполненные планы и рабочие черновики не переносились в архив. (3) Устаревшие документы (decomposition) не помечены и не перенесены. Консолидация по этому отчёту уменьшает разрозненность.

**Рекомендации по GitHub:**

- В `README.md` и в индексе оставить явную ссылку: «Единая точка входа: docs/development-index.md».
- В PR-шаблоне (если будет) добавить пункт: «При закрытии задачи из Топ-5 или docs/tasks обновлены индекс и при необходимости PENDING_GAPS/RESOLVED_GAPS».
- Критичные изменения в `docs/architecture/glossary/` по-прежнему только через Lead Architect (OWNERSHIP.md).

---

## 6. Фреймворк избежания дублирования и расхождений

### 6.1 Правила, которые уже есть

- **Одна точка входа:** `docs/development-index.md`; правило `development-index-rule.mdc` с `alwaysApply: true`.
- **Приоритет при конфликте:** `docs/` и `AGENTS.md` > `.cursor/rules/` > остальное.
- **Правила обновления** в секции 4.10 индекса: при закрытии задачи — обновлять PENDING_GAPS/RESOLVED_GAPS; при фиче — project-implementation и context-tree/features; при новом решении — DECISIONS_LOG и ADR.

### 6.2 Дополнительные рекомендации

1. **Один источник правды на тип данных:**  
   - Фичи и шаги → только `project-implementation.md`.  
   - Открытые/закрытые дыры → только `PENDING_GAPS.md` / `RESOLVED_GAPS.md`.  
   - «Что делать сейчас» → только Топ-5 в индексе (при необходимости — плюс current-focus для контекста сессии).

2. **Ссылки вместо копирования:** В новых документах не копировать списки фич или Топ-5, а давать ссылку на индекс или project-implementation.

3. **Пометки об устаревании:** Если документ перестал отражать реализацию — в начало добавить блок «⚠️ Устарело» с указанием актуального источника или перенести в `docs/archive/` с поясняющим именем.

4. **Архив выполненных планов:** Планы с чек-листами (например single_development_index_and_roadmap, agent-branch-workflow-implementation) после выполнения переносить в `docs/archive/` с датой или темой, чтобы не смешивать с действующими процессами.

5. **Краткость онбординг-документов:** PROJECT_BRIEF_FOR_AGENTS и аналоги — держать в формате «кратко + ссылки», без дублирования полного стека и списков из AGENTS.md и индекса.

6. **Регулярная проверка:** Раз в спринт или при смене приоритетов проверять: актуален ли Топ-5; отмечены ли выполненные фичи в project-implementation; перенесены ли закрытые дыры в RESOLVED_GAPS; нет ли документов с устаревшей моделью (как decomposition).

---

## 7. Краткое резюме

- **Дублирование:** В основном в виде повторения «открой индекс / Топ-5» в нескольких файлах — это усиление одной точки входа. Реальное дублирование содержания — стек/структура в AGENTS, README, QWEN; целостность процесса в development-plan-and-integrity и INTEGRITY_AND_DEVELOPMENT. Рекомендации: явно развести роли (кратко/подробно), в QWEN оставить ссылки на AGENTS и индекс.
- **Противоречия:** Одно критичное — `decomposition.md` (Payment/Accrual через land_plot_id) против текущей модели (FinancialSubject). Остальные источники согласованы.
- **Иерархия:** На вершине — `docs/development-index.md` как главная дорожная карта навигации; единственный источник фич — `docs/project-implementation.md`.
- **Точки входа:** Должна быть одна — индекс; остальные входы — по ссылкам из него. Лишних «конкурирующих» точек входа не выявлено.
- **Консолидация:** Архивировать выполненные планы и development-index-work; пометить устаревшим или архивировать decomposition; в индексе явно указать связку development-plan-and-integrity ↔ INTEGRITY_AND_DEVELOPMENT.
- **GitHub:** Документация и история в Git; семантическая история — в DECISIONS_LOG, RESOLVED_GAPS, ADR. Рекомендации: явная ссылка на индекс в README и при PR.
- **Фреймворк:** Один источник правды на тип данных, ссылки вместо копирования, пометки об устаревании, архив выполненных планов, короткие онбординг-документы, периодическая проверка актуальности.

При необходимости следующий шаг — выполнить конкретные правки по плану консолидации (архивирование файлов, правка decomposition, обновление ссылок в development-index).
