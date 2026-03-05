# Списки файлов для агентов по блокам работ

Документ содержит перечни файлов, которые каждый агент должен просмотреть перед выполнением своей задачи. Пути указаны от корня репозитория.

### Рекомендация по загрузке контекста

Чтобы контекст не размывался и не создавал лишнего шума:

1. **Сначала** загрузи только блок **«Обязательный контекст проекта»** (или первый блок раздела агента) и блок **«Точки входа и границы системы»** (если есть в списке агента).
2. **Остальные файлы** подтягивай по мере необходимости: при анализе конкретной области — соответствующий подраздел; при подозрении на проблему — конкретный файл.
3. Не загружай полное содержимое всех перечисленных файлов в один контекст разом: это увеличивает токены и рассеивает внимание. Используй списки как чеклист для выборочного чтения.

---

## Формат вывода: список задач для агента-исполнителя

Каждый из трёх агентов (Архитектурный Критик, Security-Аудитор, Реалист Реализации) по итогам анализа **обязательно формирует список задач** в едином формате. Этот список передаётся **агенту-исполнителю**, который выполняет изменения в коде и документации.

### Структура списка задач

Для каждой рекомендации или замечания агент добавляет **одну или несколько задач** в следующем виде:

| Поле | Обязательность | Описание |
|------|----------------|----------|
| **id** | да | Уникальный идентификатор в рамках отчёта агента (например, `A1-1`, `S2-3`, `R3-2`). Префикс: A — архитектор, S — security, R — реалист. |
| **действие** | да | Конкретное действие в повелительном наклонении: что сделать (например: «Добавить валидацию query в эндпоинте поиска владельцев», «Вынести общую логику расчёта баланса в доменный сервис»). |
| **файлы/область** | да | Пути к файлам или область кода (например: `backend/app/modules/land_management/api/routes.py`, «все репозитории модуля accruals»). |
| **тип** | да | Один из: `architecture` \| `security` \| `refactor` \| `docs` \| `tests` \| `deps`. |
| **приоритет** | да | `high` \| `medium` \| `low`. |
| **обоснование** | рекомендуется | Кратко: почему это нужно (1–2 предложения). |
| **зависимости** | по необходимости | id других задач, которые нужно выполнить до этой (например: «после A1-2»). |

### Пример одной задачи

```markdown
- **id:** S2-1
- **действие:** Параметризовать поиск владельцев по имени/УНП в `owner_service.py`, убрать конкатенацию строк в SQL.
- **файлы:** `backend/app/services/owner_service.py`
- **тип:** security
- **приоритет:** high
- **обоснование:** Снижение риска SQL-инъекции при передаче query из API.
```

### Итоговый артефакт агента

В конце работы агент выдаёт:

1. **Краткий отчёт** (выводы по своей области).
2. **Список задач для агента-исполнителя** — в виде таблицы или маркированного списка по шаблону выше. Задачи должны быть **выполнимыми без домысливания**: исполнитель должен понимать, что именно менять и где.

Объединённые списки от всех трёх агентов передаются агенту-исполнителю как единый бэклог; приоритет и порядок выполнения можно скорректировать вручную.

---

## Агент 1: «Архитектурный Критик»

**Роль:** Старший технический архитектор. Поиск слабых мест в предложенном техническом решении или коде (масштабирование, производительность, поддержка, логические нестыковки).

### Обязательный контекст проекта

| Файл | Назначение |
|------|------------|
| `AGENTS.md` | Обзор проекта, стек, архитектура, конвенции |
| `docs/project-design.md` | Цели системы, ролевая модель, мультитенантность, принципы |
| `docs/project-implementation.md` | Дорожная карта реализации фич |
| `docs/architecture/common/system-context-l1.mmd` | Системный контекст (L1) |
| `docs/architecture/common/databases.mmd` | Модель БД в архитектуре |
| `docs/data-model/entities-minimal.md` | Минимальное описание сущностей данных |

### Точки входа и границы системы

| Файл | Назначение |
|------|------------|
| `backend/app/main.py` | Сборка FastAPI, подключение роутеров, CORS, описание API |
| `backend/app/config.py` | Настройки (БД, JWT, окружение) |
| `backend/app/db/session.py` | Движок и сессия БД, `get_db` |
| `backend/app/db/base.py` | DeclarativeBase, тип Guid (UUID) |
| `backend/app/db/register_models.py` | Регистрация ORM-моделей для Alembic/тестов |
| `frontend/vite.config.ts` | Сборка фронта, проксирование `/api` на бэкенд |
| `frontend/package.json` | Зависимости фронта |
| `backend/pyproject.toml` или `backend/requirements.txt` | Зависимости бэкенда |

### Модульная структура бэкенда (DDD / Clean Architecture)

| Файл | Назначение |
|------|------------|
| `backend/app/modules/__init__.py` | Корень модулей |
| `backend/app/modules/cooperative_core/api/routes.py` | API СТ |
| `backend/app/modules/land_management/api/routes.py` | API участков и владельцев |
| `backend/app/modules/financial_core/api/routes.py` | API финансовых субъектов |
| `backend/app/modules/accruals/api/routes.py` | API начислений |
| `backend/app/modules/payments/api/routes.py` | API платежей |
| `backend/app/modules/expenses/api/routes.py` | API расходов |
| `backend/app/modules/meters/api/routes.py` | API счётчиков |
| `backend/app/modules/reporting/api/routes.py` | API отчётов |
| `backend/app/modules/administration/api/routes.py` | API администрирования / auth |
| `backend/app/modules/shared/multitenancy/context.py` | Извлечение `cooperative_id` из контекста |
| `backend/app/modules/financial_core/domain/entities.py` | Доменные сущности финансового ядра |
| `backend/app/modules/financial_core/domain/services.py` | Доменные сервисы |
| `backend/app/modules/financial_core/infrastructure/repositories.py` | Репозитории финансового ядра |
| `backend/app/modules/land_management/application/use_cases.py` | Use cases участков/владельцев |
| `backend/app/modules/land_management/infrastructure/repositories.py` | Репозитории участков/владельцев |
| `backend/app/modules/accruals/application/use_cases.py` | Use cases начислений |
| `backend/app/modules/payments/application/use_cases.py` | Use cases платежей |
| `backend/app/modules/reporting/domain/services.py` | Сервисы отчётности |
| `backend/app/modules/reporting/infrastructure/read_models.py` | Read-модели для отчётов |

### Модели и схемы (целостность данных, транзакции)

Модели и схемы находятся в соответствующих модулях:

| Модуль | Модели | Схемы |
|--------|--------|-------|
| Accruals | `backend/app/modules/accruals/infrastructure/models.py` | `backend/app/modules/accruals/api/schemas.py` |
| Payments | `backend/app/modules/payments/infrastructure/models.py` | `backend/app/modules/payments/api/schemas.py` |
| Expenses | `backend/app/modules/expenses/infrastructure/models.py` | `backend/app/modules/expenses/api/schemas.py` |
| Land Management | `backend/app/modules/land_management/infrastructure/models.py` | `backend/app/modules/land_management/api/schemas.py` |
| Financial Core | `backend/app/modules/financial_core/infrastructure/models.py` | `backend/app/modules/financial_core/api/schemas.py` |
| Administration | `backend/app/modules/administration/infrastructure/models.py` | `backend/app/modules/administration/api/schemas.py` |

### Фронтенд (границы, состояние, вызовы API)

| Файл | Назначение |
|------|------------|
| `frontend/src/main.ts` | Точка входа приложения |
| `frontend/src/App.vue` | Корневой компонент, роутинг |
| `frontend/src/router/index.ts` | Маршруты и охрана доступа |
| `frontend/src/services/api.ts` | Axios-клиент, baseURL, перехватчики JWT/401 |
| `frontend/src/stores/auth.ts` | Состояние аутентификации, логин, хранение токена |
| `frontend/src/stores/accruals.ts` | Состояние начислений |
| `frontend/src/stores/payments.ts` | Состояние платежей |
| `frontend/src/types/index.ts` | Общие типы (User, Cooperative и т.д.) |

**Итого (Агент 1):** архитектурная документация, точка входа бэкенда/фронта, конфиг, модульные роуты и use cases, ключевые модели/схемы, мультитенантность, фронтовые store и API-клиент.

**Результат:** оформи в виде краткого отчёта и списка задач для агента-исполнителя по шаблону из раздела «Формат вывода: список задач для агента-исполнителя».

---

## Агент 2: «Security-Аудитор»

**Роль:** Специалист по ИБ. Поиск уязвимостей: SQL-инъекции, XSS, CSRF, утечки в логах, аутентификация/авторизация, валидация и экранирование ввода.

### Аутентификация и авторизация

| Файл | Назначение |
|------|------------|
| `backend/app/core/security.py` | Хеширование паролей (bcrypt), создание/декодирование JWT |
| `backend/app/api/deps.py` | OAuth2PasswordBearer, get_current_user, require_role |
| `backend/app/modules/administration/api/routes.py` | Логин, выдача токена, /me |
| `backend/app/config.py` | SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES |
| `backend/app/modules/administration/infrastructure/models.py` | Модель пользователя (роль, cooperative_id, is_active) |
| `frontend/src/stores/auth.ts` | Хранение токена в localStorage, декодирование JWT на клиенте, отправка учётных данных |
| `frontend/src/services/api.ts` | Подстановка Bearer-токена, обработка 401, baseURL |
| `frontend/src/views/LoginView.vue` | Форма логина, передача credentials в API |

### Защита API и разграничение доступа

| Файл | Назначение |
|------|------------|
| `backend/app/main.py` | CORS (allow_origins, credentials), перечень эндпоинтов |
| `backend/app/modules/administration/api/routes.py` | Регистрация/пользователи |
| `backend/app/modules/land_management/api/routes.py` | Проверка cooperative_id в use cases |
| `backend/app/modules/accruals/api/routes.py` | Передача cooperative_id из current_user |
| `backend/app/modules/payments/api/routes.py` | То же для платежей |
| `backend/app/modules/expenses/api/routes.py` | То же для расходов |
| `backend/app/modules/meters/api/routes.py` | То же для счётчиков |
| `backend/app/modules/cooperative_core/api/routes.py` | Доступ к СТ в зависимости от роли |
| `backend/app/modules/shared/multitenancy/context.py` | Получение cooperative_id из контекста (риск подмены) |

### Ввод пользователя и работа с БД

| Файл | Назначение |
|------|------------|
| `backend/app/modules/land_management/infrastructure/repositories.py` | search_by_name_or_tax_id(query) — параметризация поиска |
| `backend/app/modules/land_management/api/routes.py` | Query-параметры (query, limit, skip), body (создание участников/владельцев) |
| `backend/app/modules/financial_core/infrastructure/repositories.py` | Все execute() — только ORM/select, без raw SQL |
| `backend/app/modules/accruals/infrastructure/repositories.py` | То же |
| `backend/app/modules/payments/infrastructure/repositories.py` | То же |
| `backend/app/modules/expenses/infrastructure/repositories.py` | То же |
| `backend/app/modules/meters/infrastructure/repositories.py` | То же |
| `backend/app/modules/cooperative_core/infrastructure/repositories.py` | То же |
| `backend/app/db/session.py` | get_db, commit/rollback — нет прямого доступа к БД снаружи |

### Схемы запросов (валидация Pydantic)

| Файл | Назначение |
|------|------------|
| `backend/app/modules/land_management/api/schemas.py` | Создание/обновление владельца, участка |
| `backend/app/modules/accruals/api/schemas.py` | Создание начисления |
| `backend/app/modules/payments/application/dtos.py` | DTO платежей |
| `backend/app/modules/expenses/application/dtos.py` | DTO расходов |
| `backend/app/modules/land_management/application/dtos.py` | DTO участков/владельцев |

### Фронтенд: XSS и чувствительные данные

| Файл | Назначение |
|------|------------|
| `frontend/src/views/LoginView.vue` | Ввод пароля, отображение ошибок |
| `frontend/src/views/AccrualCreateView.vue` | Формы сумм и дат |
| `frontend/src/views/PaymentCreateView.vue` | Формы платежей |
| `frontend/src/views/ExpensesView.vue` | Отображение данных с бэкенда |
| `frontend/src/utils/errorFormatter.ts` | Форматирование ошибок (не логирование лишнего) |

### Скрипты и конфигурация

| Файл | Назначение |
|------|------------|
| `backend/app/scripts/seed_db.py` | Наполнение БД тестовыми данными (пароли, пользователи) |
| `backend/app/scripts/seed_user.py` | Создание пользователя (хеш пароля) |
| `backend/.env.example` | Пример переменных (SECRET_KEY, DATABASE_URL) — при наличии |

**Итого (Агент 2):** security-слой, deps и auth API, конфиг с секретами, все точки ввода (схемы, query, body), репозитории (проверка отсутствия raw SQL/конкатенации), мультитенантность, фронт: логин, API-клиент, формы и отображение данных, сиды.

**Результат:** оформи в виде краткого отчёта и списка задач для агента-исполнителя по шаблону из раздела «Формат вывода: список задач для агента-исполнителя».

---

## Агент 3: «Реалист Реализации»

**Роль:** Ведущий разработчик. Оценка сложности реализации и поддержки: over-engineering, зависимости, документация, тесты, сравнение с более простыми альтернативами.

### Обзор проекта и зависимости

| Файл | Назначение |
|------|------------|
| `AGENTS.md` | Стек, команды сборки/тестов, структура, pitfalls |
| `package.json` (корень) | Единый запуск backend+frontend |
| `backend/pyproject.toml` или `backend/requirements.txt` | Зависимости Python, версии |
| `frontend/package.json` | Зависимости Vue/Vite/Pinia/axios |
| `backend/app/config.py` | Настройки, источник .env |
| `backend/app/main.py` | Подключение роутеров |

### Модули и зависимости между слоями

| Файл | Назначение |
|------|------------|
| `backend/app/modules/deps.py` | Общие зависимости (если есть) для модулей |
| `backend/app/modules/land_management/application/use_cases.py` | Количество use cases, зависимости от репозиториев |
| `backend/app/modules/financial_core/application/use_cases.py` | Use cases финансового ядра |
| `backend/app/modules/expenses/application/use_cases.py` | Use cases расходов |
| `backend/app/modules/meters/application/use_cases.py` | Use cases счётчиков |
| `backend/app/modules/reporting/application/use_cases.py` | Use cases отчётов |
| `backend/app/modules/cooperative_core/application/use_cases.py` | Use cases СТ |
| `backend/app/db/session.py` | Использование сессии в репозиториях |
| `backend/app/db/register_models.py` | Список моделей для миграций |

### Документация и ADR

| Файл | Назначение |
|------|------------|
| `docs/project-design.md` | Дизайн и решения |
| `docs/project-implementation.md` | План фич |
| `docs/architecture/adr/` | Наличие и содержание ADR (каталог) |
| `docs/architecture/glossary/contributions.md` | Глоссарий домена |
| `docs/agents/backend-developer.md` | Рекомендации для бэкенд-разработчика |
| `docs/agents/frontend-developer.md` | Рекомендации для фронтенд-разработчика |

### Тесты

| Файл | Назначение |
|------|------------|
| `backend/tests/conftest.py` | Фикстуры БД, клиент, токены по ролям, переопределение get_db |
| `backend/tests/test_api/test_auth.py` | Тесты логина/me |
| `backend/tests/test_api/test_accruals.py` | Тесты API начислений |
| `backend/tests/test_api/test_payments.py` | Тесты API платежей |
| `backend/tests/test_api/test_land_plots.py` | Тесты API участков |
| `backend/tests/test_api/test_owners.py` | Тесты API владельцев |
| `backend/tests/test_api/test_expenses.py` | Тесты API расходов |
| `backend/tests/test_core/test_security.py` | Тесты security (хеш, JWT) |
| `frontend/src/main.spec.ts` | Наличие/объём unit-тестов фронта |

### Фронтенд: сложность и поддерживаемость

| Файл | Назначение |
|------|------------|
| `frontend/src/router/index.ts` | Охранные хуки, разбиение по ролям |
| `frontend/src/stores/auth.ts` | Логика логина и хранения токена |
| `frontend/src/stores/accruals.ts` | Загрузка/кэш начислений |
| `frontend/src/stores/payments.ts` | То же для платежей |
| `frontend/src/stores/landPlots.ts` | Участки |
| `frontend/src/stores/owners.ts` | Владельцы |
| `frontend/src/components/MainLayout.vue` | Общий каркас и навигация |
| `frontend/src/components/Sidebar.vue` | Меню по ролям |
| `frontend/src/views/DashboardView.vue` | Главная страница |
| `frontend/src/views/AccrualCreateView.vue` | Сложность формы создания начисления |
| `frontend/src/views/PaymentCreateView.vue` | Сложность формы платежа |

### Миграции и развёртывание

| Файл | Назначение |
|------|------------|
| `backend/alembic.ini` | Конфигурация Alembic |
| `backend/alembic/versions/` | Список миграций (порядок и объём) |
| `.github/workflows/backend-tests.yml` | CI тестов бэкенда |

**Итого (Агент 3):** обзор стека и команд, структура модулей и use cases, документация и ADR, покрытие тестами (API, security, фронт), сложность фронта (stores, формы), миграции и CI.

**Результат:** оформи в виде краткого отчёта и списка задач для агента-исполнителя по шаблону из раздела «Формат вывода: список задач для агента-исполнителя».

---

## Краткая сводка по агентам

| Агент | Фокус | Ключевые артефакты |
|-------|--------|---------------------|
| **1. Архитектурный Критик** | Масштабирование, производительность, поддержка, целостность решений | docs (design, implementation, architecture), main.py, config, модульные routes/use cases, модели/схемы, мультитенантность, фронт store/api |
| **2. Security-Аудитор** | Уязвимости, аутентификация/авторизация, валидация, БД | security.py, deps, auth API, config, все репозитории и схемы ввода, мультитенантность, фронт логин/api/формы, сиды |
| **3. Реалист Реализации** | Сложность, зависимости, тесты, документация | AGENTS.md, зависимости backend/frontend, use cases и репозитории, docs/ADR/глоссарий, tests/, миграции, CI |

При добавлении новых фич или изменении архитектуры списки можно дополнять конкретными файлами из затронутой области.

---

## Агент-исполнитель (входные данные)

Агент-исполнитель получает на вход **объединённый список задач** от одного или нескольких агентов (Критик, Security-Аудитор, Реалист). Для каждой задачи в списке:

- Выполнить действие в указанных файлах/области.
- Соблюдать тип задачи (security — не ослаблять проверки; refactor — не менять поведение; tests — добавить/обновить тесты).
- Учитывать приоритет и зависимости (id других задач): при наличии «зависимости» выполнять задачу после указанных.
- После выполнения — отметить задачу выполненной (в отчёте или чеклисте).

Рекомендуемый порядок обработки: сначала задачи с типом `security` и приоритетом `high`, затем `architecture` / `refactor`, затем `tests` и `docs`. Конфликты между рекомендациями разных агентов разрешаются вручную или по приоритету (например, security выше удобства рефакторинга).
