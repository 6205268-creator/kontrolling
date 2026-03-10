# КОНТРОЛЛИНГ — Контекст проекта

**Система учёта хозяйственной деятельности садоводческих товариществ (СТ) Республики Беларусь.**

Предназначена для управления взносами, платежами, задолженностями, учёта земельных участков, приборов учёта и формирования отчётности. Все денежные суммы указаны в **белорусских рублях (BYN)**.

---

## Технологический стек

| Уровень | Технология |
|---------|------------|
| **Backend** | Python 3.11+ • FastAPI • SQLAlchemy 2.0 (async) • Alembic • PostgreSQL 15+ (asyncpg) |
| **Frontend** | Vue 3 + TypeScript • Vite • Pinia • Vue Router |
| **Auth** | JWT + bcrypt (python-jose, passlib) |
| **Тесты** | pytest + pytest-asyncio (backend) • Vitest (frontend) • Playwright (e2e) |
| **Linting** | ruff (длина строки 100, target py311) |

---

## Структура проекта

```
kontrolling/
├── backend/                    # FastAPI приложение
│   ├── app/
│   │   ├── main.py             # Фабрика FastAPI приложения
│   │   ├── config.py           # Конфигурация на pydantic-settings
│   │   ├── db/                 # DB сессии, базовая модель
│   │   ├── api/deps.py         # Общие зависимости
│   │   └── modules/            # Модули Clean Architecture (9 доменов)
│   ├── tests/                  # Тесты backend (197 тестов)
│   ├── alembic/                # Миграции БД
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                   # Vue 3 SPA (15 представлений, 6 Pinia stores)
│   ├── src/
│   ├── e2e/                    # Playwright e2e тесты
│   └── package.json
├── docs/                       # Подробная документация
│   ├── development-index.md    # Единая точка входа (НАЧАТЬ ОТСЮДА)
│   ├── project-design.md       # Архитектура системы
│   ├── project-implementation.md # Дорожная карта (35/35 завершено)
│   ├── data-model/             # ER-диаграммы, просмотрщик схемы
│   ├── architecture/           # ADR, глоссарии, политика окружений
│   ├── plan/                   # Текущий фокус, workflow-документы
│   ├── tasks/                  # Файлы задач, спецификации, чек-листы
│   └── history/                # PENDING_GAPS, RESOLVED_GAPS
├── .cursor/rules/              # Правила для агентов Cursor
│   ├── agents/                 # Правила для ролей
│   ├── git-branch-policy.mdc   # Правило работы с ветками
│   └── architecture-guardian.mdc # Правило ревью архитектуры
├── docker-compose.yml          # Развёртывание полного стека
├── package.json                # Скрипты разработки (npm run dev)
└── QWEN.md                     # Этот файл
```

---

## Сборка и запуск

### Единый запуск (рекомендуется)

Из **корня проекта** одновременно запускаются backend (порт 8000) и frontend (порт 5173):

```powershell
# Однократная настройка
npm install

# Запуск обоих сервисов (Windows)
npm run dev
```

Доступ: **http://localhost:5173** (frontend проксирует `/api` на backend).

### Только Backend

**Всегда запускайте backend из каталога `backend/`** — конфиг читает `.env` относительно текущей рабочей директории.

```powershell
# Создать/активировать venv (однократно)
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

# Установить зависимости
pip install -e ".[dev]"

# Запуск dev-сервера
uvicorn app.main:app --reload

# Запуск тестов (используется in-memory SQLite — PostgreSQL не требуется)
pytest
pytest tests/test_health.py::test_health_returns_ok

# Миграции Alembic
alembic revision --autogenerate -m "описание"
alembic upgrade head

# Lint
ruff check .
ruff format --check .
```

### Только Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Развёртывание в Docker

```bash
docker compose up --build -d
```

Запускаются только **db** и **backend**. Frontend запускается отдельно: из корня `npm run dev`, затем открыть http://localhost:5173.

Доступ:
- **Frontend:** http://localhost:5173 (после `npm run dev`)
- **Backend API:** http://localhost:8000
- **Swagger документация:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/api/health

---

## Наполнение БД тестовыми данными

**Каноническая точка входа** — скрипт `seed_db.py` создаёт полный тестовый набор данных (2 товарищества, владельцы, участки, пользователи, начисления, платежи, расходы, счётчики). Идемпотентен.

```powershell
cd backend
python -m app.scripts.seed_db
```

---

## Архитектура

### Шаблон модуля Clean Architecture

Каждый модуль в `backend/app/modules/` следует структуре:

```
{module_name}/
├── domain/           # Чистый Python (сущности, репозитории, события)
│   ├── entities.py
│   ├── repositories.py
│   └── events.py
├── application/      # Use cases и DTOs
│   ├── use_cases.py
│   └── dtos.py
├── infrastructure/   # Реализации, зависящие от фреймворков
│   ├── models.py     # SQLAlchemy ORM модели
│   └── repositories.py # Реализации репозиториев
└── api/              # FastAPI слой
    ├── routes.py
    └── schemas.py
```

### Модули

| Модуль | Назначение |
|--------|------------|
| `cooperative_core` | Управление товариществами |
| `land_management` | Земельные участки, владельцы, владения |
| `financial_core` | Финансовые субъекты, балансы |
| `accruals` | Взносы и начисления |
| `payments` | Обработка платежей |
| `expenses` | Учёт расходов |
| `meters` | Приборы учёта и показания |
| `reporting` | Отчёты и аналитика |
| `administration` | Аутентификация и пользователи |

### Ключевые доменные концепции

- **Cooperative** — садоводческое товарищество (СТ); граница арендатора
- **LandPlot** — земельный участок в пределах товарищества
- **Owner** — физическое или юридическое лицо; связано с участками через **PlotOwnership** (нет прямого FK)
- **PlotOwnership** — запись о владении с долями (`share_numerator/share_denominator`), `is_primary` = член СТ
- **FinancialSubject** — центральная финансовая абстракция; все `Accrual` и `Payment` проходят через него (никогда напрямую к участку/счётчику)
- **Multi-tenancy** — на уровне данных через `cooperative_id` на LandPlot, FinancialSubject, Expense

---

## Соглашения разработки

### Стиль кода

- **Длина строки:** 100 символов
- **Python target:** 3.11
- **Диаграммы:** Только Mermaid (без PlantUML)
- **Именование C4:** Префиксы `Person_`, `Service_`, `System_`, `Database_`

### Тестирование

- **Backend:** `pytest` из `backend/` (использует in-memory SQLite)
- **Fixtures:** `test_db`, `async_client`, токены ролей в `tests/conftest.py`
- **Критично:** Установить `DATABASE_URL` и импортировать модели **до** импорта `app.main` в тестах

### Архитектурные правила

- **Schema First:** Обновлять диаграммы **до** изменений кода
- **Мягкое удаление:** Финансовые сущности используют `status = archived|cancelled`; жёсткое удаление запрещено
- **ADR обязательно:** Каждое значимое архитектурное решение требует ADR
- **Владение глоссариями:** Только Lead Architect может редактировать файлы глоссариев
- **Не выдумывать бизнес-требования:** Спрашивать при неясности

### Pre-Commit чек-лист

Перед коммитом проверить:

- [ ] `pytest` — все тесты зелёные
- [ ] `ruff check .` — без ошибок
- [ ] `ruff format --check .` — форматирование OK
- [ ] `python -m app.scripts.architecture_linter` — все проверки пройдены (exit code 0)
- [ ] `python -m app.scripts.seed_db` — тестовые данные созданы без ошибок
- [ ] Диаграммы обновлены (если менялась модель данных)
- [ ] Ограниченные пути не затронуты (или одобрено Lead Architect)

---

## Workflow агентов (изолированные задачи)

Для любой изолированной задачи (фичи, рефакторинг, исправления ошибок):

### 1. Политика веток

- **Никогда не коммитить в `main` или `master`**
- Работать только в указанной feature-ветке
- Merge в main только после явного одобрения пользователя
- Если ветка не существует → спросить пользователя перед созданием
- Если ветка существует → проверить статус, показать последние 5 коммитов, спросить подтверждение

**Файл правила:** `.cursor/rules/git-branch-policy.mdc`

### 2. Выполнение этапов

Для каждого этапа многоэтапной задачи:

1. Агент выводит план этапа, ждёт «yes»/«start»
2. Вносит изменения в рабочую ветку
3. Запускает проверки по порядку:
   - `pytest` (все тесты зелёные)
   - `ruff check .` + `ruff format --check .` (без ошибок)
   - `python -m app.scripts.architecture_linter` (exit code 0)
   - `python -m app.scripts.seed_db` (без ошибок)
4. Вызывает `@architecture-guardian` для ревью
5. Исправляет ошибки (минорные → сразу, серьёзные → после подтверждения пользователя)
6. Переходит к следующему этапу только после прохождения всех проверок

**Документ workflow:** `docs/plan/agent-isolated-task-workflow.md`

### 3. Рвью Architecture Guardian

После каждого этапа вызвать `@architecture-guardian` для проверки:

1. **Границы слоёв** — API не импортирует из infrastructure
2. **Финансовое ядро** — Accrual/Payment используют FinancialSubject
3. **Модель данных** — модели зарегистрированы в `register_models.py`
4. **Тесты** — все тесты проходят, новая логика покрыта
5. **Диаграммы** — обновлены при изменении модели

**Файл правила:** `.cursor/rules/agents/architecture-guardian.mdc`

---

## Индекс документации

| Документ | Описание |
|----------|----------|
| [`docs/development-index.md`](docs/development-index.md) | **НАЧАТЬ ОТСЮДА** — Единая точка входа, Топ-5 задач, дорожная карта |
| [`docs/project-design.md`](docs/project-design.md) | Полный дизайн системы |
| [`docs/project-implementation.md`](docs/project-implementation.md) | Дорожная карта фич (35/35 завершено) |
| [`docs/data-model/schema-viewer.html`](docs/data-model/schema-viewer.html) | Интерактивный просмотрщик схемы |
| [`docs/architecture/environment-policy.md`](docs/architecture/environment-policy.md) | Политика окружений |
| [`docs/architecture/adr/README.md`](docs/architecture/adr/README.md) | Процесс ADR |
| [`docs/plan/current-focus.md`](docs/plan/current-focus.md) | Текущий фокус задач, workflow-документы |
| [`docs/tasks/workflow-orchestration.md`](docs/tasks/workflow-orchestration.md) | Оркестрация workflow, pre-commit чек-лист |

---

## Для AI-ассистентов

### Context7 MCP (использовать всегда)

Для **любой документации библиотек/API** (FastAPI, SQLAlchemy, Vue, Pydantic, pytest, Alembic, httpx и т.д.) **всегда** использовать Context7 MCP — не полагаться на знания модели.

Конфиг: `.cursor/mcp.json` | Правило: `.cursor/rules/context7-docs.mdc`

### Цитирование кода

Использовать формат: `startLine:endLine:путь/к/файлу` (например, `12:15:backend/app/main.py`)

### Язык

Отвечать на **русском языке**, если пользователь не запросил иное.

### Правила

Проектные правила в `.cursor/rules/` — следовать при применимости:

| Правило | Назначение |
|---------|------------|
| `.cursor/rules/git-branch-policy.mdc` | Workflow веток для изолированных задач |
| `.cursor/rules/architecture-guardian.mdc` | Чек-лист ревью архитектуры |
| `.cursor/rules/development-index-rule.mdc` | Всегда читать development index первым |
| `.cursor/rules/project-conventions.mdc` | SOLID, KISS, никаких выдуманных требований |
| `.cursor/rules/agents/` | 10 промптов для ролей (backend, frontend, QA, DevOps и др.) |

---

## Быстрый справочник

```powershell
# Полная dev-среда (Windows)
npm install                          # Корневые зависимости
cd backend && python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd ..
npm run dev                          # Запуск обоих сервисов

# Наполнение БД
cd backend && python -m app.scripts.seed_db

# Запуск тестов
cd backend && pytest

# Архитектурный линтер
cd backend && python -m app.scripts.architecture_linter

# Развёртывание в Docker
docker compose up --build -d
```

---

## Статус проекта

- **Backend:** ✅ 35/35 фич завершено (100%)
- **Тесты:** ✅ 176 тестов проходят, 5 skipped
- **Frontend:** ✅ 15 представлений, 6 Pinia stores, Playwright e2e
- **Docker:** ✅ Готово к развёртыванию полного стека
- **Документация:** ✅ Подробная (development index, ADR, глоссарии)
- **Workflow агентов:** ✅ Политика веток + architecture guardian реализованы

**Следующие приоритеты:**
1. Заполнение глоссариев (7 из 10 доменов ожидают — низкий приоритет)
2. Миграция frontend на Clean Architecture (пост-MVP)
3. Расширение покрытия e2e тестами
4. Документация OpenAPI (пост-MVP)
5. Верификация e2e прохождения в Docker

---

## Текущий фокус задачи

**Ledger-ready MVP** — временная финансовая модель, необратимость операций, баланс на дату, подготовка к переходу на ledger.

- **Ветка:** `feature/ledger-ready-mvp`
- **Статус:** Спецификация готова, реализация не начата
- **Этапы:** 5 (модель → правило баланса → отмена → защита amount → domain events)
- **Спецификация:** `docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`
- **Фокус:** `docs/plan/current-focus.md`
