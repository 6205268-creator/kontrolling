# Краткое описание проекта КОНТРОЛЛИНГ — для передачи агенту

**Назначение:** этот файл можно передать другому агенту (или человеку), чтобы быстро ввести в контекст и задавать уточняющие вопросы. В нём — суть проекта и **единый стержень**, который не даёт проекту развалиться на разрозненные дорожные карты и контексты.

**Дата:** 2026-03-04

---

## 1. Что это за проект

**КОНТРОЛЛИНГ** — система учёта для **садоводческих товариществ (СТ)** в Беларуси.

- **Деньги:** только BYN, без мультивалюты.
- **Кто пользуется:** владельцы участков, казначей, председатель СТ.
- **Что делают:** учёт взносов, платежей, расходов, участков, владельцев, счётчиков, отчётность.

**Проблема, которую решаем:** Excel-таблицы, ручной учёт, потеря истории при смене казначея, непрозрачность для владельцев. Система даёт единую базу, личные кабинеты, автоматические начисления и отчёты.

---

## 2. Технологии (без деталей)

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 15+ (asyncpg).
- **Frontend:** Vue 3 + TypeScript + Vite + Pinia (15 views, 6 stores, Playwright e2e).
- **Auth:** JWT + bcrypt.
- **Тесты:** pytest (backend, 197 тестов), Vitest (frontend), Playwright e2e.
- **Сборка/деплой:** Docker, GitHub Actions (backend/frontend tests).

Backend — модульная Clean Architecture по доменам (cooperative_core, land_management, financial_core, accruals, payments, expenses, meters, reporting, administration). Модели живут в модулях (`infrastructure/models.py`), не в общем `app.models`.

---

## 3. Единый стержень проекта (главное для порядка)

Чтобы проект не расползался на разные «дорожные карты» и контексты, есть **одна точка входа** и чёткая иерархия источников «что делать дальше».

### 3.1 Единая точка входа

**Файл:** [`docs/development-index.md`](development-index.md)

- Содержит: **Топ-5 задач**, дорожную карту по фичам, ссылки на архитектуру, задания по ролям, инфраструктуру, архив.
- Правило для агентов: **перед работой над планом, фичей или архитектурой — прочитать этот документ.**
- Правило зафиксировано в `.cursor/rules/development-index-rule.mdc` (alwaysApply: true).

### 3.2 Иерархия «что дальше»

```
docs/development-index.md          ← стержень: «Топ-5: что делать прямо сейчас»
  ├── docs/project-implementation.md   ← полный backlog фич (35 фич, все выполнены)
  ├── docs/history/PENDING_GAPS.md     ← открытые дыры (сейчас 1: глоссарии)
  ├── docs/history/RESOLVED_GAPS.md   ← закрытые дыры
  └── docs/tasks/                     ← задания по командам (TASK_*, todo, e2e-setup и т.д.)
```

**Простое правило:** открыть `development-index.md` → смотреть «Топ-5» → брать задачу → работать. При закрытии задачи — обновлять PENDING_GAPS/RESOLVED_GAPS и при необходимости «Топ-5».

### 3.3 Дорожная карта по фичам

- **Канонический источник:** [`docs/project-implementation.md`](project-implementation.md).
- **Статус:** 35 из 35 фич бэкенда завершены (100%). Дальше — фронтенд (фазы 1–4), E2E, глоссарии, OpenAPI и т.д., см. Топ-5 в индексе.

Конфликт данных между документами: приоритет у `docs/` и `AGENTS.md`, затем `.cursor/rules/`, остальное — ниже.

---

## 4. Ключевые моменты (чтобы задавать правильные вопросы)

| Тема | Суть |
|------|------|
| **Мультитенантность** | По данным: `cooperative_id` на LandPlot, FinancialSubject, Expense; владелец (Owner) не привязан к СТ напрямую — только через участки (PlotOwnership). |
| **Финансы** | Все начисления и платежи идут через **FinancialSubject**, не напрямую к участку или счётчику. |
| **Участки и владельцы** | Связь участок–владелец только через **PlotOwnership** (доли share_numerator/denominator, is_primary). |
| **Удаление** | Для финансовых сущностей — мягкое удаление (status archived/cancelled), жёсткое удаление запрещено. |
| **Seed данных** | Канонический скрипт — `python -m app.scripts.seed_db` (идемпотентен). Отдельно `seed_user.py` — только пользователь admin при необходимости. |
| **Тесты backend** | В CI — in-memory SQLite (`conftest.py` переопределяет DATABASE_URL до импорта app). PostgreSQL в CI для unit/API не требуется. |
| **Окружение** | Конфиг читается из `backend/.env`; backend нужно запускать из каталога `backend/`, чтобы путь к .env был верный. Политика: [`docs/architecture/environment-policy.md`](architecture/environment-policy.md). |
| **Роли агентов** | Описаны в `.cursor/rules/agents/` (backend, frontend, QA, DevOps, security, UX/UI, project-orchestrator, seo). Порядок работы команд: `agent-team-tasks-order.mdc`. |
| **Глоссарии и ADR** | Глоссарии по доменам — только Lead Architect (`docs/architecture/glossary/`). ADR — индекс и процесс в `docs/architecture/adr/README.md`. |
| **Бизнес-требования** | Не придумывать. При неясных источниках данных, формулах или процессах — остановиться, задать вопросы, явно перечислить недостающую информацию. |

---

## 5. Куда смотреть дальше (если агент задаёт вопросы)

- **«Что делать в первую очередь?»** → [`docs/development-index.md`](development-index.md), секция Топ-5.
- **«Как устроена реализация по фичам?»** → [`docs/project-implementation.md`](project-implementation.md).
- **«Какие дыры открыты?»** → [`docs/history/PENDING_GAPS.md`](history/PENDING_GAPS.md).
- **«Как устроен бэкенд и стек?»** → [`AGENTS.md`](../AGENTS.md), [`docs/project-design.md`](project-design.md), [`docs/architecture/system-patterns.md`](architecture/system-patterns.md).
- **«Модель данных?»** → [`docs/data-model/`](data-model/) (в т.ч. schema-viewer.html, entities-minimal.md).
- **«Правила для агентов и обновления индекса?»** → [`development-index-rule.mdc`](../.cursor/rules/development-index-rule.mdc), секция «Правила обновления» в [`docs/development-index.md`](development-index.md).

---

## 6. Итог одной фразой

**Проект держится на одном стержне:** `docs/development-index.md` с Топ-5 и ссылками на дорожную карту, дыры и задания. Все агенты и разработчики должны опираться на него, чтобы не разнести контекст по разным «картам» и не потерять порядок.

Если нужно что-то уточнить по проекту — используй этот файл как оглавление и задавай вопросы по разделам выше; ответы и детали ищи в указанных документах.
