# Controlling — План реализации

**Цель:** Создать систему учёта хозяйственной деятельности садоводческих товариществ (СТ) с веб-интерфейсом для управления участками, начислениями, платежами и отчётностью.

**Технологический стек:**
- Backend: FastAPI 0.129.0 + Python 3.11+
- Database: PostgreSQL 15+ + SQLAlchemy 2.0 (async) + Alembic
- Frontend: Vue 3 + TypeScript + Vite + Pinia
- Auth: JWT + bcrypt
- Testing: pytest + pytest-asyncio (backend), Vitest (frontend)

## Процесс выполнения

**Изучи контекст:**
- Для **экономии токенов**: при работе по одной фиче загружай только пакет контекста из `docs/context-tree/features/Fxx.md` (xx = номер фичи) и секцию этой фичи в данном файле. Полный дизайн и entities — по необходимости.
- Иначе: `docs/project-design.md`, `docs/data-model/entities-minimal.md`, и найди первую незакрытую фичу в плане.

**Выполни фичу:**
- Выполни все шаги фичи последовательно
- Тесты обязательны для каждой фичи
- Используй точные пути к файлам
- Следуй принципам DRY и YAGNI

**Подведи итог:**
- Напиши короткий итог: что сделал, что работает, есть ли проблемы
- Жди подтверждения пользователя
- После подтверждения: отметь шаги `- [x]` и поставь ✅ в заголовке фичи

## Принципы

- **DRY** — не дублируй код, выноси общее в функции/классы
- **YAGNI** — не добавляй то, что не описано в дизайне
- **Schema First** — сначала модель данных, потом код
- **Async-first** — используй async/await везде, где возможно
- **Type Safety** — строгая типизация (Pydantic v2, TypeScript)

---

### ✅ Фича 1: Инициализация проекта и базовая структура

**Цель:** Создать структуру проекта с настройками окружения, базовой конфигурацией FastAPI и PostgreSQL, миграциями Alembic.

**Файлы:**
- Создать: `backend/pyproject.toml`, `backend/requirements.txt`
- Создать: `backend/app/main.py`, `backend/app/config.py`
- Создать: `backend/app/db/session.py`, `backend/app/db/base.py`
- Создать: `backend/.env.example`, `backend/.gitignore`
- Создать: `backend/alembic.ini`, `backend/alembic/env.py`
- Создать: `backend/tests/conftest.py`

**Шаги:**

- [x] Создать структуру директорий backend:
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── db/
  │   │   ├── __init__.py
  │   │   ├── base.py
  │   │   └── session.py
  │   ├── models/
  │   │   └── __init__.py
  │   ├── schemas/
  │   │   └── __init__.py
  │   ├── api/
  │   │   ├── __init__.py
  │   │   └── deps.py
  │   └── core/
  │       └── __init__.py
  ├── alembic/
  │   ├── versions/
  │   └── env.py
  ├── tests/
  │   ├── __init__.py
  │   └── conftest.py
  ├── .env.example
  ├── .gitignore
  ├── alembic.ini
  ├── pyproject.toml
  └── requirements.txt
  ```

- [x] Создать `backend/requirements.txt` с зависимостями:
  ```
  fastapi[standard]==0.129.0
  uvicorn[standard]>=0.30.0
  sqlalchemy[asyncio]>=2.0.36
  asyncpg>=0.30.0
  alembic>=1.13.0
  pydantic>=2.9.0
  pydantic-settings>=2.5.0
  python-jose[cryptography]>=3.3.0
  passlib[bcrypt]>=1.7.4
  python-multipart>=0.0.9
  pytest>=8.3.0
  pytest-asyncio>=0.24.0
  httpx>=0.27.0
  ```

- [x] Создать `backend/app/config.py` с настройками через Pydantic BaseSettings:
  - `DATABASE_URL` (PostgreSQL async connection string; для Supabase — Connection pool URI с префиксом `postgresql+asyncpg://`, см. AGENTS.md)
  - `SECRET_KEY` для JWT
  - `ALGORITHM` = "HS256"
  - `ACCESS_TOKEN_EXPIRE_MINUTES` = 30
  - `PROJECT_NAME` = "Controlling API"

- [x] Создать `backend/app/db/session.py` с async engine и session maker:
  - `create_async_engine` с asyncpg драйвером
  - `async_sessionmaker` для создания сессий
  - Функция `get_db()` как dependency для FastAPI

- [x] Создать `backend/app/db/base.py` с DeclarativeBase для SQLAlchemy моделей

- [x] Создать `backend/app/main.py` с базовым FastAPI приложением:
  - Инициализация FastAPI с title, version, docs_url
  - Health check endpoint `GET /api/health`
  - CORS middleware для фронтенда

- [x] Настроить Alembic:
  - Создать `backend/alembic.ini` с sqlalchemy.url из env
  - Настроить `backend/alembic/env.py` для async миграций
  - Импортировать Base из `app.db.base`

- [x] Создать `.env.example` с шаблоном переменных окружения

- [x] Создать `.gitignore` для Python проектов (venv, __pycache__, .env, *.pyc, .pytest_cache)

- [x] Создать `backend/tests/conftest.py` с базовыми фикстурами:
  - `async_client` — AsyncClient для тестирования эндпоинтов
  - `test_db` — тестовая БД (SQLite in-memory или отдельная Postgres)

**Проверка:**
- [x] `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` — установка зависимостей успешна
- [x] `uvicorn app.main:app --reload` — сервер запускается на http://127.0.0.1:8000
- [x] `curl http://127.0.0.1:8000/api/health` — возвращает `{"status": "ok"}`
- [x] `pytest` — тесты проходят (минимум 1 тест health check)

---

### ✅ Фича 2: Модели данных — Cooperative и Owner

**Цель:** Создать SQLAlchemy модели для сущностей Cooperative (СТ) и Owner (владелец), настроить первую миграцию Alembic.

**Файлы:**
- Создать: `backend/app/models/cooperative.py`
- Создать: `backend/app/models/owner.py`
- Создать: `backend/alembic/versions/0001_init_cooperative_owner.py` (через alembic revision)
- Создать: `backend/tests/test_models/test_cooperative.py`
- Создать: `backend/tests/test_models/test_owner.py`

**Шаги:**

- [x] Создать модель `Cooperative` в `backend/app/models/cooperative.py`:
  - `id: UUID` (primary key, default uuid4)
  - `name: str` (не null, индекс)
  - `unp: str` (УНП, уникальный, опционально)
  - `address: str` (опционально)
  - `created_at: datetime` (default now)
  - `updated_at: datetime` (onupdate now)

- [x] Создать модель `Owner` в `backend/app/models/owner.py`:
  - `id: UUID` (primary key)
  - `owner_type: str` (enum: "physical", "legal")
  - `name: str` (ФИО или название организации, не null)
  - `tax_id: str` (УНП/ИД, опционально, индекс)
  - `contact_phone: str` (опционально)
  - `contact_email: str` (опционально)
  - `created_at: datetime`
  - `updated_at: datetime`

- [x] Обновить `backend/app/models/__init__.py` — импортировать все модели для Alembic

- [x] Создать миграцию: `alembic revision --autogenerate -m "init cooperative and owner"`

- [x] Применить миграцию: `alembic upgrade head`

- [x] Написать тест `backend/tests/test_models/test_cooperative.py`:
  - Создание Cooperative
  - Проверка уникальности UNP
  - Проверка автозаполнения created_at

- [x] Написать тест `backend/tests/test_models/test_owner.py`:
  - Создание Owner с типом "physical"
  - Создание Owner с типом "legal"
  - Валидация owner_type enum

**Проверка:**
- [x] `alembic upgrade head` — миграция применяется без ошибок
- [x] `psql -d controlling -c "\dt"` — таблицы `cooperatives` и `owners` созданы
- [x] `pytest tests/test_models/` — все тесты моделей проходят

---

### ✅ Фича 3: Модели данных — LandPlot и PlotOwnership

**Цель:** Создать модели участка (LandPlot) и права собственности (PlotOwnership) с валидацией долей.

**Файлы:**
- Создать: `backend/app/models/land_plot.py`
- Создать: `backend/app/models/plot_ownership.py`
- Создать: `backend/alembic/versions/0002_add_land_plot_ownership.py`
- Создать: `backend/tests/test_models/test_land_plot.py`
- Создать: `backend/tests/test_models/test_plot_ownership.py`

**Шаги:**

- [x] Создать модель `LandPlot` в `backend/app/models/land_plot.py`:
  - `id: UUID`
  - `cooperative_id: UUID` (FK на Cooperative, индекс, не null)
  - `plot_number: str` (не null, индекс)
  - `area_sqm: Decimal` (площадь в кв.м, не null)
  - `cadastral_number: str` (опционально)
  - `status: str` (enum: "active", "vacant", "archived", default "active")
  - `created_at: datetime`
  - `updated_at: datetime`
  - Уникальный индекс на `(cooperative_id, plot_number)`
  - Relationship к `Cooperative`

- [x] Создать модель `PlotOwnership` в `backend/app/models/plot_ownership.py`:
  - `id: UUID`
  - `land_plot_id: UUID` (FK на LandPlot, не null, индекс)
  - `owner_id: UUID` (FK на Owner, не null, индекс)
  - `share_numerator: int` (числитель доли, не null, >= 1)
  - `share_denominator: int` (знаменатель доли, не null, >= 1)
  - `is_primary: bool` (основной владелец = член СТ, default False)
  - `valid_from: date` (дата регистрации, не null)
  - `valid_to: date` (опционально, дата прекращения)
  - `created_at: datetime`
  - Relationships к `LandPlot` и `Owner`
  - Check constraint: `share_numerator <= share_denominator`

- [x] Создать миграцию: `alembic revision --autogenerate -m "add land_plot and plot_ownership"`

- [x] Применить миграцию: `alembic upgrade head`

- [x] Написать тест `backend/tests/test_models/test_land_plot.py`:
  - Создание LandPlot с привязкой к Cooperative
  - Проверка уникальности plot_number в рамках одного СТ
  - Валидация статуса

- [x] Написать тест `backend/tests/test_models/test_plot_ownership.py`:
  - Создание PlotOwnership с долей 1/1
  - Создание нескольких владельцев с долями 1/2, 1/2
  - Проверка constraint на share_numerator <= share_denominator
  - Проверка is_primary (только один primary на участок)

**Проверка:**
- [x] `alembic upgrade head` — миграция применяется
- [x] `psql -d controlling -c "\d land_plots"` — таблица создана с FK
- [x] `psql -d controlling -c "\d plot_ownerships"` — таблица создана с constraints
- [x] `pytest tests/test_models/` — все тесты проходят

---

### ✅ Фича 4: Модели данных — FinancialSubject (финансовое ядро)

**Цель:** Создать модель FinancialSubject — центр финансовой ответственности для всех бизнес-объектов.

**Файлы:**
- Создать: `backend/app/models/financial_subject.py`
- Создать: `backend/alembic/versions/0003_add_financial_subject.py`
- Создать: `backend/tests/test_models/test_financial_subject.py`

**Шаги:**

- [x] Создать модель `FinancialSubject` в `backend/app/models/financial_subject.py`:
  - `id: UUID`
  - `subject_type: str` (enum: "LAND_PLOT", "WATER_METER", "ELECTRICITY_METER", "GENERAL_DECISION")
  - `subject_id: UUID` (ID бизнес-объекта, не null)
  - `cooperative_id: UUID` (FK на Cooperative, индекс, не null)
  - `code: str` (уникальный код для платёжных документов, не null, уникальный)
  - `status: str` (enum: "active", "closed", default "active")
  - `created_at: datetime`
  - Уникальный индекс на `(subject_type, subject_id, cooperative_id)`
  - Relationship к `Cooperative`

- [x] Добавить функцию генерации `code` (например, `FS-{short_uuid}` или по паттерну СТ)

- [x] Создать миграцию: `alembic revision --autogenerate -m "add financial_subject"`

- [x] Применить миграцию: `alembic upgrade head`

- [x] Написать тест `backend/tests/test_models/test_financial_subject.py`:
  - Создание FinancialSubject для LAND_PLOT
  - Проверка уникальности комбинации (subject_type, subject_id, cooperative_id)
  - Проверка уникальности code
  - Валидация subject_type enum

**Проверка:**
- [x] `alembic upgrade head` — миграция применяется
- [x] `psql -d controlling -c "\d financial_subjects"` — таблица с unique constraints
- [x] `pytest tests/test_models/test_financial_subject.py` — тесты проходят

---

### ✅ Фича 5: Модели данных — Accrual и Payment

**Цель:** Создать модели начислений (Accrual) и платежей (Payment), работающие через FinancialSubject.

**Файлы:**
- Создать: `backend/app/models/contribution_type.py`
- Создать: `backend/app/models/accrual.py`
- Создать: `backend/app/models/payment.py`
- Создать: `backend/alembic/versions/0004_add_accrual_payment.py`
- Создать: `backend/tests/test_models/test_accrual.py`
- Создать: `backend/tests/test_models/test_payment.py`

**Шаги:**

- [x] Создать модель `ContributionType` в `backend/app/models/contribution_type.py`:
  - `id: UUID`
  - `name: str` (название вида взноса: "Членский", "Целевой" и т.д., не null)
  - `code: str` (уникальный код, не null)
  - `description: str` (опционально)
  - `created_at: datetime`

- [x] Создать модель `Accrual` в `backend/app/models/accrual.py`:
  - `id: UUID`
  - `financial_subject_id: UUID` (FK на FinancialSubject, индекс, не null)
  - `contribution_type_id: UUID` (FK на ContributionType, индекс, не null)
  - `amount: Decimal` (сумма в BYN, не null, >= 0)
  - `accrual_date: date` (дата начисления, не null)
  - `period_start: date` (начало периода, не null)
  - `period_end: date` (конец периода, опционально)
  - `status: str` (enum: "created", "applied", "cancelled", default "created")
  - `created_at: datetime`
  - `updated_at: datetime`
  - Relationships к `FinancialSubject` и `ContributionType`

- [x] Создать модель `Payment` в `backend/app/models/payment.py`:
  - `id: UUID`
  - `financial_subject_id: UUID` (FK на FinancialSubject, индекс, не null)
  - `payer_owner_id: UUID` (FK на Owner, индекс, не null, кто заплатил)
  - `amount: Decimal` (сумма в BYN, не null, > 0)
  - `payment_date: date` (дата платежа, не null)
  - `document_number: str` (номер документа извне, опционально)
  - `description: str` (опционально)
  - `status: str` (enum: "confirmed", "cancelled", default "confirmed")
  - `created_at: datetime`
  - `updated_at: datetime`
  - Relationships к `FinancialSubject` и `Owner`

- [x] Создать миграцию: `alembic revision --autogenerate -m "add contribution_type, accrual, payment"`

- [x] Применить миграцию: `alembic upgrade head`

- [x] Написать тест `backend/tests/test_models/test_accrual.py`:
  - Создание Accrual с привязкой к FinancialSubject
  - Проверка статусов (created → applied → cancelled)
  - Валидация amount >= 0

- [x] Написать тест `backend/tests/test_models/test_payment.py`:
  - Создание Payment с привязкой к FinancialSubject и Owner
  - Проверка статусов (confirmed → cancelled)
  - Валидация amount > 0

**Проверка:**
- [x] `alembic upgrade head` — миграция применяется
- [x] `psql -d controlling -c "\d accruals"` — таблица создана
- [x] `psql -d controlling -c "\d payments"` — таблица создана
- [x] `pytest tests/test_models/` — все тесты проходят

---

### ✅ Фича 6: Модели данных — Expense (расходы СТ)

**Цель:** Создать модели для учёта расходов товарищества (отдельный финансовый поток).

**Файлы:**
- Создать: `backend/app/models/expense_category.py`
- Создать: `backend/app/models/expense.py`
- Создать: `backend/alembic/versions/0005_add_expense.py`
- Создать: `backend/tests/test_models/test_expense.py`

**Шаги:**

- [x] Создать модель `ExpenseCategory` в `backend/app/models/expense_category.py`:
  - `id: UUID`
  - `name: str` (название категории: "Дороги", "Зарплата" и т.д., не null)
  - `code: str` (уникальный код, не null)
  - `description: str` (опционально)
  - `created_at: datetime`

- [x] Создать модель `Expense` в `backend/app/models/expense.py`:
  - `id: UUID`
  - `cooperative_id: UUID` (FK на Cooperative, индекс, не null)
  - `category_id: UUID` (FK на ExpenseCategory, индекс, не null)
  - `amount: Decimal` (сумма в BYN, не null, > 0)
  - `expense_date: date` (дата расхода, не null)
  - `document_number: str` (номер платёжного поручения/чека, опционально)
  - `description: str` (опционально)
  - `status: str` (enum: "created", "confirmed", "cancelled", default "created")
  - `created_at: datetime`
  - `updated_at: datetime`
  - Relationships к `Cooperative` и `ExpenseCategory`

- [x] Создать миграцию: `alembic revision --autogenerate -m "add expense_category and expense"`

- [x] Применить миграцию: `alembic upgrade head`

- [x] Написать тест `backend/tests/test_models/test_expense.py`:
  - Создание ExpenseCategory
  - Создание Expense с привязкой к Cooperative и Category
  - Проверка статусов
  - Валидация amount > 0

**Проверка:**
- [x] `alembic upgrade head` — миграция применяется
- [x] `psql -d controlling -c "\d expenses"` — таблица создана
- [x] `pytest tests/test_models/test_expense.py` — тесты проходят

---

### ✅ Фича 7: Модели данных — Meter и MeterReading (приборы учёта)

**Цель:** Создать модели для счётчиков воды и электричества с показаниями.

**Файлы:**
- Создать: `backend/app/models/meter.py`
- Создать: `backend/app/models/meter_reading.py`
- Создать: `backend/alembic/versions/0006_add_meter.py`
- Создать: `backend/tests/test_models/test_meter.py`

**Шаги:**

- [x] Создать модель `Meter` в `backend/app/models/meter.py`:
  - `id: UUID`
  - `owner_id: UUID` (FK на Owner, индекс, не null)
  - `meter_type: str` (enum: "WATER", "ELECTRICITY")
  - `serial_number: str` (серийный номер, опционально)
  - `installation_date: date` (опционально)
  - `status: str` (enum: "active", "inactive", default "active")
  - `created_at: datetime`
  - `updated_at: datetime`
  - Relationship к `Owner`

- [x] Создать модель `MeterReading` в `backend/app/models/meter_reading.py`:
  - `id: UUID`
  - `meter_id: UUID` (FK на Meter, индекс, не null)
  - `reading_value: Decimal` (показание, не null, >= 0)
  - `reading_date: date` (дата снятия показания, не null)
  - `created_at: datetime`
  - Relationship к `Meter`
  - Уникальный индекс на `(meter_id, reading_date)` (одно показание на дату)

- [x] Создать миграцию: `alembic revision --autogenerate -m "add meter and meter_reading"`

- [x] Применить миграцию: `alembic upgrade head`

- [x] Написать тест `backend/tests/test_models/test_meter.py`:
  - Создание Meter с привязкой к Owner
  - Создание MeterReading
  - Проверка уникальности (meter_id, reading_date)
  - Валидация reading_value >= 0

**Проверка:**
- [x] `alembic upgrade head` — миграция применяется
- [x] `psql -d controlling -c "\d meters"` — таблица создана
- [x] `psql -d controlling -c "\d meter_readings"` — таблица создана
- [x] `pytest tests/test_models/test_meter.py` — тесты проходят

---

### ✅ Фича 8: Модели данных — AppUser и роли (аутентификация)

**Цель:** Создать модель пользователя с ролями и хешированием пароля.

**Файлы:**
- Создать: `backend/app/models/app_user.py`
- Создать: `backend/app/core/security.py`
- Создать: `backend/alembic/versions/0007_add_app_user.py`
- Создать: `backend/tests/test_models/test_app_user.py`
- Создать: `backend/tests/test_core/test_security.py`

**Шаги:**

- [x] Создать `backend/app/core/security.py` с функциями:
  - `get_password_hash(password: str) -> str` — хеширование через bcrypt
  - `verify_password(plain_password: str, hashed_password: str) -> bool` — проверка пароля
  - `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str` — создание JWT
  - `decode_access_token(token: str) -> dict` — декодирование JWT

- [x] Создать модель `AppUser` в `backend/app/models/app_user.py`:
  - `id: UUID`
  - `username: str` (уникальный, не null, индекс)
  - `email: str` (уникальный, не null)
  - `hashed_password: str` (не null)
  - `role: str` (enum: "admin", "chairman", "treasurer", default "treasurer")
  - `cooperative_id: UUID` (FK на Cooperative, индекс, nullable для admin)
  - `is_active: bool` (default True)
  - `created_at: datetime`
  - `updated_at: datetime`
  - Relationship к `Cooperative`

- [x] Создать миграцию: `alembic revision --autogenerate -m "add app_user"`

- [x] Применить миграцию: `alembic upgrade head`

- [x] Написать тест `backend/tests/test_core/test_security.py`:
  - Тест хеширования пароля
  - Тест верификации пароля
  - Тест создания JWT токена
  - Тест декодирования токена

- [x] Написать тест `backend/tests/test_models/test_app_user.py`:
  - Создание AppUser с ролью "treasurer"
  - Проверка уникальности username и email
  - Валидация роли enum

**Проверка:**
- [x] `alembic upgrade head` — миграция применяется
- [x] `psql -d controlling -c "\d app_users"` — таблица создана
- [x] `pytest tests/test_core/test_security.py` — тесты безопасности проходят
- [x] `pytest tests/test_models/test_app_user.py` — тесты модели проходят

---

### ✅ Фича 9: Pydantic схемы для API (базовые схемы)

**Цель:** Создать Pydantic схемы для валидации и сериализации данных API.

**Файлы:**
- Создать: `backend/app/schemas/cooperative.py`
- Создать: `backend/app/schemas/owner.py`
- Создать: `backend/app/schemas/land_plot.py`
- Создать: `backend/app/schemas/financial_subject.py`
- Создать: `backend/app/schemas/auth.py`
- Создать: `backend/tests/test_schemas/test_cooperative.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/cooperative.py`:
  - `CooperativeBase(BaseModel)` — базовые поля (name, unp, address)
  - `CooperativeCreate(CooperativeBase)` — для создания
  - `CooperativeUpdate(BaseModel)` — для обновления (все поля Optional)
  - `CooperativeInDB(CooperativeBase)` — с id, created_at, updated_at
  - Настроить `model_config = ConfigDict(from_attributes=True)`

- [x] Создать схемы в `backend/app/schemas/owner.py`:
  - `OwnerBase` — owner_type, name, tax_id, contact_phone, contact_email
  - `OwnerCreate(OwnerBase)`
  - `OwnerUpdate(BaseModel)` — все поля Optional
  - `OwnerInDB(OwnerBase)` — с id, created_at, updated_at

- [x] Создать схемы в `backend/app/schemas/land_plot.py`:
  - `LandPlotBase` — cooperative_id, plot_number, area_sqm, cadastral_number, status
  - `LandPlotCreate(LandPlotBase)`
  - `LandPlotUpdate(BaseModel)` — все поля Optional
  - `LandPlotInDB(LandPlotBase)` — с id, created_at, updated_at

- [x] Создать схемы в `backend/app/schemas/financial_subject.py`:
  - `FinancialSubjectBase` — subject_type, subject_id, cooperative_id, code, status
  - `FinancialSubjectCreate(FinancialSubjectBase)`
  - `FinancialSubjectInDB(FinancialSubjectBase)` — с id, created_at

- [x] Создать схемы в `backend/app/schemas/auth.py`:
  - `Token(BaseModel)` — access_token: str, token_type: str = "bearer"
  - `TokenData(BaseModel)` — username: str | None, role: str | None
  - `UserLogin(BaseModel)` — username: str, password: str

- [x] Написать тест `backend/tests/test_schemas/test_cooperative.py`:
  - Валидация CooperativeCreate
  - Сериализация CooperativeInDB из SQLAlchemy модели

**Проверка:**
- [x] `pytest tests/test_schemas/` — тесты схем проходят
- [x] Импорт всех схем без ошибок

---

### ✅ Фича 10: API endpoints — Authentication (JWT)

**Цель:** Реализовать эндпоинты для логина и получения JWT токена.

**Файлы:**
- Создать: `backend/app/api/v1/__init__.py`
- Создать: `backend/app/api/v1/auth.py`
- Изменить: `backend/app/api/deps.py` — добавить `get_current_user` dependency
- Изменить: `backend/app/main.py` — подключить auth router
- Создать: `backend/tests/test_api/test_auth.py`

**Шаги:**

- [x] Создать структуру API:
  ```
  backend/app/api/
  ├── __init__.py
  ├── deps.py
  └── v1/
      ├── __init__.py
      └── auth.py
  ```

- [x] Реализовать `backend/app/api/deps.py`:
  - `get_db()` — async generator для DB session
  - `get_current_user(token: str = Depends(OAuth2PasswordBearer))` — декодирует JWT, возвращает AppUser
  - `require_role(allowed_roles: list[str])` — проверка роли пользователя

- [x] Реализовать `backend/app/api/v1/auth.py`:
  - `POST /api/v1/auth/login` — принимает username и password, возвращает Token
  - Логика: найти пользователя по username, проверить пароль, создать JWT
  - Возвращает `{"access_token": "...", "token_type": "bearer"}`

- [x] Подключить router в `backend/app/main.py`:
  - `app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])`

- [x] Написать тест `backend/tests/test_api/test_auth.py`:
  - Создать тестового пользователя в БД
  - Тест успешного логина с валидными credentials
  - Тест неуспешного логина с неверным паролем
  - Тест получения текущего пользователя с валидным токеном
  - Тест 401 при невалидном токене

**Проверка:**
- [x] `uvicorn app.main:app --reload` — сервер запускается
- [x] `curl -X POST http://127.0.0.1:8000/api/v1/auth/login -d '{"username":"test","password":"test"}'` — возвращает токен
- [x] `pytest tests/test_api/test_auth.py` — все тесты проходят

---

### ✅ Фича 11: API endpoints — Cooperatives (CRUD)

**Цель:** Реализовать CRUD операции для Cooperative с разграничением по ролям.

**Файлы:**
- Создать: `backend/app/api/v1/cooperatives.py`
- Создать: `backend/app/services/cooperative_service.py`
- Изменить: `backend/app/main.py` — подключить cooperatives router
- Создать: `backend/tests/test_api/test_cooperatives.py`
- Создать: `backend/tests/test_services/test_cooperative_service.py`

**Шаги:**

- [x] Создать `backend/app/services/cooperative_service.py` (Service Layer):
  - `async def create_cooperative(db: AsyncSession, cooperative: CooperativeCreate) -> Cooperative`
  - `async def get_cooperative(db: AsyncSession, cooperative_id: UUID) -> Cooperative | None`
  - `async def get_cooperatives(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Cooperative]`
  - `async def update_cooperative(db: AsyncSession, cooperative_id: UUID, data: CooperativeUpdate) -> Cooperative`
  - `async def delete_cooperative(db: AsyncSession, cooperative_id: UUID) -> bool`

- [x] Написать тест `backend/tests/test_services/test_cooperative_service.py`:
  - Тест создания Cooperative
  - Тест получения списка
  - Тест обновления
  - Тест удаления

- [x] Создать `backend/app/api/v1/cooperatives.py`:
  - `GET /api/v1/cooperatives/` — список СТ (admin видит все, chairman/treasurer только своё)
  - `POST /api/v1/cooperatives/` — создать СТ (только admin)
  - `GET /api/v1/cooperatives/{id}` — получить СТ по ID
  - `PATCH /api/v1/cooperatives/{id}` — обновить СТ (только admin)
  - `DELETE /api/v1/cooperatives/{id}` — удалить СТ (только admin)

- [x] Реализовать фильтрацию по cooperative_id для chairman/treasurer в get_current_user

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_cooperatives.py`:
  - Тест создания СТ от имени admin
  - Тест получения списка от имени treasurer (видит только своё)
  - Тест получения списка от имени admin (видит все)
  - Тест 403 при попытке treasurer создать СТ

**Проверка:**
- [x] `pytest tests/test_services/test_cooperative_service.py` — тесты сервиса проходят
- [x] `pytest tests/test_api/test_cooperatives.py` — тесты API проходят
- [x] `curl -H "Authorization: Bearer {token}" http://127.0.0.1:8000/api/v1/cooperatives/` — возвращает список СТ

---

### ✅ Фича 12: API endpoints — Owners (CRUD)

**Цель:** Реализовать CRUD операции для Owner.

**Файлы:**
- Создать: `backend/app/api/v1/owners.py`
- Создать: `backend/app/services/owner_service.py`
- Изменить: `backend/app/main.py` — подключить owners router
- Создать: `backend/tests/test_api/test_owners.py`

**Шаги:**

- [x] Создать `backend/app/services/owner_service.py`:
  - `async def create_owner(db: AsyncSession, owner: OwnerCreate) -> Owner`
  - `async def get_owner(db: AsyncSession, owner_id: UUID) -> Owner | None`
  - `async def get_owners(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Owner]`
  - `async def update_owner(db: AsyncSession, owner_id: UUID, data: OwnerUpdate) -> Owner`
  - `async def search_owners(db: AsyncSession, query: str) -> list[Owner]` — поиск по имени/tax_id

- [x] Создать `backend/app/api/v1/owners.py`:
  - `GET /api/v1/owners/` — список владельцев
  - `POST /api/v1/owners/` — создать владельца (treasurer, admin)
  - `GET /api/v1/owners/{id}` — получить владельца
  - `PATCH /api/v1/owners/{id}` — обновить владельца (treasurer, admin)
  - `GET /api/v1/owners/search?q={query}` — поиск владельцев

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_owners.py`:
  - Тест создания Owner
  - Тест получения списка
  - Тест поиска по имени
  - Тест обновления

**Проверка:**
- [x] `pytest tests/test_api/test_owners.py` — тесты проходят (13 тестов)
- [x] `curl -H "Authorization: Bearer {token}" http://127.0.0.1:8000/api/v1/owners/` — возвращает список

---

### ✅ Фича 13: API endpoints — LandPlots (CRUD с PlotOwnership)

**Цель:** Реализовать CRUD для участков с поддержкой множественных владельцев.

**Файлы:**
- Создать: `backend/app/schemas/plot_ownership.py`
- Создать: `backend/app/api/v1/land_plots.py`
- Создать: `backend/app/services/land_plot_service.py`
- Изменить: `backend/app/main.py`
- Создать: `backend/tests/test_api/test_land_plots.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/plot_ownership.py`:
  - `PlotOwnershipBase` — owner_id, share_numerator, share_denominator, is_primary, valid_from, valid_to
  - `PlotOwnershipCreate(PlotOwnershipBase)` — с land_plot_id (опционально)
  - `PlotOwnershipInDB(PlotOwnershipBase)` — с id, created_at

- [x] Создать `backend/app/services/land_plot_service.py`:
  - `async def create_land_plot(db: AsyncSession, plot: LandPlotCreate, ownerships: list[PlotOwnershipCreate]) -> LandPlot`
  - При создании участка автоматически создать FinancialSubject (subject_type="LAND_PLOT")
  - `async def get_land_plots_by_cooperative(db: AsyncSession, cooperative_id: UUID) -> list[LandPlot]`
  - `async def get_land_plot_with_owners(db: AsyncSession, plot_id: UUID) -> dict` — участок + список владельцев
  - `async def add_plot_ownership(db: AsyncSession, ownership: PlotOwnershipCreate) -> PlotOwnership`
  - `async def close_plot_ownership(db: AsyncSession, ownership_id: UUID, valid_to: date) -> PlotOwnership` — закрыть владение

- [x] Создать `backend/app/api/v1/land_plots.py`:
  - `GET /api/v1/land-plots/` — список участков (фильтр по cooperative_id)
  - `POST /api/v1/land-plots/` — создать участок с владельцами (treasurer, admin)
  - `GET /api/v1/land-plots/{id}` — получить участок с владельцами и финансовым субъектом
  - `PATCH /api/v1/land-plots/{id}` — обновить участок
  - `POST /api/v1/land-plots/{id}/ownerships` — добавить владельца к участку
  - `PATCH /api/v1/land-plots/ownerships/{id}/close` — закрыть право собственности

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_land_plots.py`:
  - Тест создания участка с одним владельцем
  - Тест создания участка с несколькими владельцами (доли 1/2, 1/2)
  - Тест получения участка с владельцами
  - Тест добавления нового владельца
  - Тест закрытия владения (установка valid_to)

**Проверка:**
- [x] `pytest tests/test_api/test_land_plots.py` — тесты проходят (13 тестов)
- [x] При создании участка автоматически создаётся FinancialSubject

---

### ✅ Фича 14: API endpoints — FinancialSubjects и балансы

**Цель:** Реализовать просмотр финансовых субъектов и расчёт балансов.

**Файлы:**
- Создать: `backend/app/api/v1/financial_subjects.py`
- Создать: `backend/app/services/balance_service.py`
- Создать: `backend/app/schemas/balance.py`
- Изменить: `backend/app/main.py`
- Создать: `backend/tests/test_services/test_balance_service.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/balance.py`:
  - `BalanceInfo(BaseModel)`:
    - `financial_subject_id: UUID`
    - `total_accruals: Decimal`
    - `total_payments: Decimal`
    - `balance: Decimal` (задолженность = accruals - payments)
    - `subject_type: str`
    - `subject_id: UUID`
    - `cooperative_id: UUID`
    - `code: str`

- [x] Создать `backend/app/services/balance_service.py`:
  - `async def calculate_balance(db: AsyncSession, financial_subject_id: UUID) -> BalanceInfo`
  - Сумма всех Accrual со статусом "applied"
  - Минус сумма всех Payment со статусом "confirmed"
  - `async def get_balances_by_cooperative(db: AsyncSession, cooperative_id: UUID) -> list[BalanceInfo]`

- [x] Написать тест `backend/tests/test_services/test_balance_service.py`:
  - Создать FinancialSubject, Accrual, Payment
  - Проверить расчёт баланса
  - Тест с несколькими начислениями и платежами

- [x] Создать `backend/app/api/v1/financial_subjects.py`:
  - `GET /api/v1/financial-subjects/` — список финансовых субъектов (фильтр по cooperative_id)
  - `GET /api/v1/financial-subjects/{id}/balance` — баланс конкретного субъекта
  - `GET /api/v1/financial-subjects/balances?cooperative_id={id}` — балансы всех субъектов СТ

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_financial_subjects.py`:
  - Тест получения баланса
  - Тест получения списка балансов по СТ

**Проверка:**
- [x] `pytest tests/test_services/test_balance_service.py` — тесты расчёта проходят (7 тестов)
- [x] `pytest tests/test_api/test_financial_subjects.py` — тесты API проходят (7 тестов)

---

### ✅ Фича 15: API endpoints — Accruals (начисления)

**Цель:** Реализовать создание и управление начислениями.

**Файлы:**
- Создать: `backend/app/schemas/accrual.py`
- Создать: `backend/app/api/v1/accruals.py`
- Создать: `backend/app/services/accrual_service.py`
- Изменить: `backend/app/main.py`
- Создать: `backend/tests/test_api/test_accruals.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/accrual.py`:
  - `AccrualBase` — financial_subject_id, contribution_type_id, amount, accrual_date, period_start, period_end
  - `AccrualCreate(AccrualBase)`
  - `AccrualInDB(AccrualBase)` — с id, status, created_at, updated_at
  - `AccrualBatchCreate` — для массового создания

- [x] Создать `backend/app/services/accrual_service.py`:
  - `async def create_accrual(db: AsyncSession, accrual: AccrualCreate) -> Accrual`
  - При создании статус = "created"
  - `async def apply_accrual(db: AsyncSession, accrual_id: UUID) -> Accrual` — изменить статус на "applied"
  - `async def cancel_accrual(db: AsyncSession, accrual_id: UUID) -> Accrual` — изменить статус на "cancelled"
  - `async def get_accruals_by_financial_subject(db: AsyncSession, fs_id: UUID) -> list[Accrual]`
  - `async def get_accruals_by_cooperative(db: AsyncSession, cooperative_id: UUID) -> list[Accrual]`
  - `async def mass_create_accruals(db: AsyncSession, accruals: list[AccrualCreate]) -> list[Accrual]` — массовое создание

- [x] Создать `backend/app/api/v1/accruals.py`:
  - `POST /api/v1/accruals/` — создать начисление (treasurer, admin)
  - `POST /api/v1/accruals/batch` — массовое создание (treasurer, admin)
  - `POST /api/v1/accruals/{id}/apply` — применить начисление
  - `POST /api/v1/accruals/{id}/cancel` — отменить начисление
  - `GET /api/v1/accruals/?financial_subject_id={id}` — список начислений по финансовому субъекту
  - `GET /api/v1/accruals/?cooperative_id={id}` — список начислений по СТ

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_accruals.py`:
  - Тест создания начисления
  - Тест применения начисления (created → applied)
  - Тест отмены начисления
  - Тест отмены уже отменённого (400)
  - Тест применения уже применённого (400)
  - Тест массового создания
  - Тест получения по финансовому субъекту
  - Тест получения по СТ
  - Тест 403 для чужого СТ

**Проверка:**
- [x] `pytest tests/test_api/test_accruals.py` — тесты проходят (10 тестов)
- [x] Статусы начислений корректно меняются

---

### ✅ Фича 16: API endpoints — Payments (платежи)

**Цель:** Реализовать регистрацию платежей и отмену.

**Файлы:**
- Создать: `backend/app/schemas/payment.py`
- Создать: `backend/app/api/v1/payments.py`
- Создать: `backend/app/services/payment_service.py`
- Изменить: `backend/app/main.py`
- Создать: `backend/tests/test_api/test_payments.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/payment.py`:
  - `PaymentBase` — financial_subject_id, payer_owner_id, amount, payment_date, document_number, description
  - `PaymentCreate(PaymentBase)`
  - `PaymentInDB(PaymentBase)` — с id, status, created_at, updated_at

- [x] Создать `backend/app/services/payment_service.py`:
  - `async def register_payment(db: AsyncSession, payment: PaymentCreate) -> Payment`
  - При создании статус = "confirmed"
  - `async def cancel_payment(db: AsyncSession, payment_id: UUID) -> Payment` — изменить статус на "cancelled"
  - `async def get_payments_by_financial_subject(db: AsyncSession, fs_id: UUID) -> list[Payment]`
  - `async def get_payments_by_owner(db: AsyncSession, owner_id: UUID) -> list[Payment]` — платежи владельца
  - `async def get_payments_by_cooperative(db: AsyncSession, cooperative_id: UUID) -> list[Payment]`

- [x] Создать `backend/app/api/v1/payments.py`:
  - `POST /api/v1/payments/` — зарегистрировать платёж (treasurer, admin)
  - `POST /api/v1/payments/{id}/cancel` — отменить платёж (treasurer, admin)
  - `GET /api/v1/payments/?financial_subject_id={id}` — список платежей по финансовому субъекту
  - `GET /api/v1/payments/?owner_id={id}` — платежи владельца
  - `GET /api/v1/payments/?cooperative_id={id}` — платежи по СТ

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_payments.py`:
  - Тест регистрации платежа
  - Тест отмены платежа
  - Тест отмены уже отменённого (400)
  - Тест получения платежей по финансовому субъекту
  - Тест получения платежей владельца
  - Тест получения платежей по СТ
  - Тест 403 для чужого СТ
  - Тест 400 без параметров
  - Тест 422 при сумме <= 0
  - Тест для treasurer (своё СТ)

**Проверка:**
- [x] `pytest tests/test_api/test_payments.py` — тесты проходят (10 тестов)
- [x] После регистрации платежа баланс пересчитывается корректно (учитывается в balance_service)

---

### ✅ Фича 17: API endpoints — Expenses (расходы СТ)

**Цель:** Реализовать учёт расходов товарищества.

**Файлы:**
- Создать: `backend/app/schemas/expense.py`
- Создать: `backend/app/api/v1/expenses.py`
- Создать: `backend/app/services/expense_service.py`
- Изменить: `backend/app/main.py`
- Создать: `backend/tests/test_api/test_expenses.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/expense.py`:
  - `ExpenseCategoryBase` — name, code, description
  - `ExpenseCategoryInDB(ExpenseCategoryBase)` — с id, created_at
  - `ExpenseBase` — cooperative_id, category_id, amount, expense_date, document_number, description
  - `ExpenseCreate(ExpenseBase)`
  - `ExpenseInDB(ExpenseBase)` — с id, status, created_at, updated_at

- [x] Создать `backend/app/services/expense_service.py`:
  - `async def create_expense(db: AsyncSession, expense: ExpenseCreate) -> Expense`
  - `async def confirm_expense(db: AsyncSession, expense_id: UUID) -> Expense` — статус "confirmed"
  - `async def cancel_expense(db: AsyncSession, expense_id: UUID) -> Expense` — статус "cancelled"
  - `async def get_expenses_by_cooperative(db: AsyncSession, coop_id: UUID) -> list[Expense]`
  - `async def get_expense_categories(db: AsyncSession) -> list[ExpenseCategory]`

- [x] Создать `backend/app/api/v1/expenses.py`:
  - `GET /api/v1/expenses/categories` — список категорий расходов
  - `POST /api/v1/expenses/` — создать расход (treasurer, admin)
  - `POST /api/v1/expenses/{id}/confirm` — подтвердить расход
  - `POST /api/v1/expenses/{id}/cancel` — отменить расход
  - `GET /api/v1/expenses/?cooperative_id={id}` — список расходов по СТ

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_expenses.py`:
  - Тест получения категорий
  - Тест создания расхода
  - Тест подтверждения расхода (created → confirmed)
  - Тест отмены расхода (confirmed → cancelled)
  - Тест отмены уже отменённого (400)
  - Тест подтверждения уже подтверждённого (400)
  - Тест получения расходов по СТ
  - Тест 403 для чужого СТ
  - Тест 422 при сумме <= 0
  - Тест для treasurer (auto cooperative_id)
  - Тест 404 при несуществующей категории

**Проверка:**
- [x] `pytest tests/test_api/test_expenses.py` — тесты проходят (11 тестов)
- [x] Расходы не влияют на баланс FinancialSubject (отдельный поток)

---

### ✅ Фича 18: API endpoints — Meters и показания

**Цель:** Реализовать управление счётчиками и снятие показаний.

**Файлы:**
- Создать: `backend/app/schemas/meter.py`
- Создать: `backend/app/api/v1/meters.py`
- Создать: `backend/app/services/meter_service.py`
- Изменить: `backend/app/main.py`
- Создать: `backend/tests/test_api/test_meters.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/meter.py`:
  - `MeterBase` — owner_id, meter_type, serial_number, installation_date, status
  - `MeterCreate(MeterBase)`
  - `MeterInDB(MeterBase)` — с id, created_at, updated_at
  - `MeterReadingBase` — meter_id, reading_value, reading_date
  - `MeterReadingCreate(MeterReadingBase)`
  - `MeterReadingInDB(MeterReadingBase)` — с id, created_at

- [x] Создать `backend/app/services/meter_service.py`:
  - `async def create_meter(db: AsyncSession, meter: MeterCreate) -> Meter`
  - При создании счётчика автоматически создать FinancialSubject (subject_type="WATER_METER" или "ELECTRICITY_METER")
  - `async def get_meters_by_owner(db: AsyncSession, owner_id: UUID) -> list[Meter]`
  - `async def add_meter_reading(db: AsyncSession, reading: MeterReadingCreate) -> MeterReading`
  - `async def get_meter_readings(db: AsyncSession, meter_id: UUID) -> list[MeterReading]` — история показаний

- [x] Создать `backend/app/api/v1/meters.py`:
  - `POST /api/v1/meters/` — создать счётчик (treasurer, admin)
  - `GET /api/v1/meters/?owner_id={id}` — список счётчиков владельца
  - `GET /api/v1/meters/{id}` — получить счётчик
  - `POST /api/v1/meters/{id}/readings` — добавить показание
  - `GET /api/v1/meters/{id}/readings` — история показаний

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_meters.py`:
  - Тест создания счётчика (WATER и ELECTRICITY)
  - Тест автоматического создания FinancialSubject при создании счётчика
  - Тест добавления показания
  - Тест получения истории показаний
  - Тест 400 при дублировании даты показания
  - Тест 400 при несуществующем владельце
  - Тест 400 без owner_id

**Проверка:**
- [x] `pytest tests/test_api/test_meters.py` — тесты проходят (11 тестов)
- [x] При создании счётчика создаётся FinancialSubject (если у владельца есть участок)

---

### ✅ Фича 19: API endpoints — Reports (базовые отчёты)

**Цель:** Реализовать базовые отчёты: должники, движение средств.

**Файлы:**
- Создать: `backend/app/api/v1/reports.py`
- Создать: `backend/app/services/report_service.py`
- Создать: `backend/app/schemas/report.py`
- Изменить: `backend/app/main.py`
- Создать: `backend/tests/test_api/test_reports.py`

**Шаги:**

- [x] Создать схемы в `backend/app/schemas/report.py`:
  - `DebtorInfo(BaseModel)`:
    - `financial_subject_id: UUID`
    - `subject_type: str`
    - `subject_info: dict` (информация о бизнес-объекте: plot_number или meter serial)
    - `owner_name: str`
    - `total_debt: Decimal`
  - `CashFlowReport(BaseModel)`:
    - `period_start: date`
    - `period_end: date`
    - `total_accruals: Decimal`
    - `total_payments: Decimal`
    - `total_expenses: Decimal`
    - `net_balance: Decimal`

- [x] Создать `backend/app/services/report_service.py`:
  - `async def get_debtors_report(db: AsyncSession, cooperative_id: UUID, min_debt: Decimal = 0) -> list[DebtorInfo]`
  - Выбрать все FinancialSubject с балансом > min_debt
  - `async def get_cash_flow_report(db: AsyncSession, cooperative_id: UUID, period_start: date, period_end: date) -> CashFlowReport`
  - Суммы начислений, платежей, расходов за период

- [x] Создать `backend/app/api/v1/reports.py`:
  - `GET /api/v1/reports/debtors?cooperative_id={id}&min_debt={amount}` — отчёт по должникам
  - `GET /api/v1/reports/cash-flow?cooperative_id={id}&period_start={date}&period_end={date}` — отчёт о движении средств
  - Доступ: chairman, treasurer, admin

- [x] Подключить router в `backend/app/main.py`

- [x] Написать тест `backend/tests/test_api/test_reports.py`:
  - Создать тестовые данные: участки, начисления, платежи, расходы
  - Тест отчёта по должникам
  - Тест отчёта о движении средств

**Проверка:**
- [x] `pytest tests/test_api/test_reports.py` — тесты проходят (11 тестов)
- [x] Отчёты возвращают корректные данные

---

### ✅ Фича 20: Frontend — Инициализация Vue 3 проекта

**Цель:** Создать структуру frontend проекта на Vue 3 + TypeScript + Vite + Pinia.

**Файлы:**
- Создать: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`
- Создать: `frontend/src/main.ts`, `frontend/src/App.vue`
- Создать: `frontend/src/router/index.ts`
- Создать: `frontend/src/stores/auth.ts`
- Создать: `frontend/index.html`

**Шаги:**

- [x] Создать проект: `cd frontend && npm create vite@latest . -- --template vue-ts`

- [x] Установить зависимости:
  ```
  npm install
  npm install vue-router@4 pinia axios
  npm install -D @types/node
  ```

- [x] Создать структуру директорий:
  ```
  frontend/
  ├── src/
  │   ├── main.ts
  │   ├── App.vue
  │   ├── router/
  │   │   └── index.ts
  │   ├── stores/
  │   │   └── auth.ts
  │   ├── views/
  │   │   ├── LoginView.vue
  │   │   └── DashboardView.vue
  │   ├── components/
  │   ├── services/
  │   │   └── api.ts
  │   └── types/
  │       └── index.ts
  ├── index.html
  ├── package.json
  ├── tsconfig.json
  ├── vite.config.ts
  └── .env.development
  ```

- [x] Создать `frontend/src/services/api.ts` с axios instance:
  - Base URL из env: `VITE_API_BASE_URL`
  - Interceptor для добавления JWT токена в headers

- [x] Создать `frontend/src/stores/auth.ts` (Pinia store):
  - `state: { token: string | null, user: User | null }`
  - `actions: { login(username, password), logout(), checkAuth() }`
  - Сохранение токена в localStorage

- [x] Создать `frontend/src/router/index.ts`:
  - Роуты: `/login`, `/dashboard`
  - Navigation guard для проверки аутентификации

- [x] Создать `frontend/.env.development`:
  - `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`

- [x] Настроить CORS на бэкенде для `http://localhost:5173`

**Проверка:**
- [x] `cd frontend && npm run dev` — dev сервер запускается на http://localhost:5173
- [x] `npm run build` — сборка проходит без ошибок
- [x] Axios делает запросы на backend без CORS ошибок

---

### ✅ Фича 21: Frontend — Страница логина

**Цель:** Реализовать форму логина с JWT аутентификацией.

**Файлы:**
- Создать: `frontend/src/views/LoginView.vue`
- Изменить: `frontend/src/stores/auth.ts` — доработать login action
- Изменить: `frontend/src/router/index.ts` — добавить роут `/login`

**Шаги:**

- [x] Создать `frontend/src/views/LoginView.vue`:
  - Форма с полями username и password
  - Кнопка "Войти"
  - Обработка ошибок (401 — неверные credentials)
  - При успешном логине — редирект на `/dashboard`

- [x] Реализовать `login` action в `frontend/src/stores/auth.ts`:
  - `POST /api/v1/auth/login` с username и password
  - Сохранение токена в localStorage и state
  - Получение текущего пользователя (роль, cooperative_id)

- [x] Добавить роут в `frontend/src/router/index.ts`:
  - `/login` → `LoginView.vue`

- [x] Стилизовать форму (базовый CSS или подключить UI библиотеку, например, PrimeVue или Element Plus)

**Проверка:**
- [x] Открыть http://localhost:5173/login
- [x] Ввести валидные credentials — успешный логин, редирект на dashboard
- [x] Ввести неверный пароль — отображается ошибка
- [x] Токен сохраняется в localStorage

---

### ✅ Фича 22: Frontend — Dashboard и навигация

**Цель:** Создать основную структуру приложения с навигацией по разделам.

**Файлы:**
- Создать: `frontend/src/views/DashboardView.vue`
- Создать: `frontend/src/components/MainLayout.vue`
- Создать: `frontend/src/components/Sidebar.vue`
- Изменить: `frontend/src/router/index.ts` — добавить дочерние роуты

**Шаги:**

- [x] Создать `frontend/src/components/MainLayout.vue`:
  - Sidebar с навигацией
  - Верхний header с именем пользователя и кнопкой "Выйти"
  - `<router-view>` для контента

- [x] Создать `frontend/src/components/Sidebar.vue`:
  - Меню с разделами:
    - Участки
    - Владельцы
    - Начисления
    - Платежи
    - Расходы
    - Счётчики
    - Отчёты
  - Пункты меню зависят от роли пользователя (chairman не видит "Создать платёж")

- [x] Создать `frontend/src/views/DashboardView.vue` — главная страница после логина

- [x] Настроить роуты в `frontend/src/router/index.ts`:
  - `/` → `MainLayout` (layout с sidebar)
    - `/dashboard` → `DashboardView`
    - `/land-plots` → `LandPlotsView` (создадим позже)
    - `/owners` → `OwnersView`
    - и т.д.

- [x] Добавить navigation guard: если нет токена — редирект на `/login`

**Проверка:**
- [x] После логина отображается dashboard с sidebar
- [x] Клик по пунктам меню переключает разделы
- [x] Кнопка "Выйти" очищает токен и редиректит на login

---

### ✅ Фича 23: Frontend — Список участков (LandPlots)

**Цель:** Отобразить список участков с фильтрацией по СТ.

**Файлы:**
- Создать: `frontend/src/views/LandPlotsView.vue`
- Создать: `frontend/src/stores/landPlots.ts`
- Создать: `frontend/src/types/index.ts` — типы для LandPlot, Owner и т.д.

**Шаги:**

- [x] Создать типы в `frontend/src/types/index.ts`:
  - `interface LandPlot { id: string; cooperative_id: string; plot_number: string; area_sqm: number; status: string; ... }`
  - `interface Owner { id: string; name: string; owner_type: string; ... }`

- [x] Создать Pinia store `frontend/src/stores/landPlots.ts`:
  - `state: { plots: LandPlot[], loading: boolean }`
  - `actions: { fetchPlots(cooperativeId: string), createPlot(data) }`

- [x] Создать `frontend/src/views/LandPlotsView.vue`:
  - Таблица со списком участков: номер участка, площадь, статус, владельцы
  - Кнопка "Добавить участок" (для treasurer, admin)
  - Фильтр по СТ (для admin, chairman/treasurer видят только своё СТ)

- [x] Вызвать `fetchPlots` при монтировании компонента

**Проверка:**
- [x] Открыть `/land-plots` — отображается таблица участков
- [x] Данные загружаются из API
- [x] Пагинация и сортировка работают (если реализовано)

---

### ✅ Фича 24: Frontend — Создание участка с владельцами

**Цель:** Реализовать форму создания участка с поддержкой множественных владельцев.

**Файлы:**
- Создать: `frontend/src/views/LandPlotCreateView.vue`
- Изменить: `frontend/src/router/index.ts` — добавить роут `/land-plots/create`

**Шаги:**

- [x] Создать `frontend/src/views/LandPlotCreateView.vue`:
  - Форма с полями: plot_number, area_sqm, cadastral_number, status
  - Выбор СТ (для admin) или автоматически cooperative_id текущего пользователя
  - Секция "Владельцы":
    - Поиск владельца по имени (автокомплит через API)
    - Добавление владельца с указанием доли (numerator/denominator)
    - Checkbox "Основной владелец" (is_primary)
    - Кнопка "Добавить ещё владельца"
  - Кнопка "Создать участок"

- [x] Валидация:
  - Хотя бы один владелец
  - Сумма долей = 1 (опционально)
  - Только один владелец с is_primary = true

- [x] При сабмите вызвать `POST /api/v1/land-plots/` с данными участка и владельцев

- [x] После успешного создания — редирект на `/land-plots`

**Проверка:**
- [x] Форма отображается корректно
- [x] Поиск владельцев работает
- [x] Создание участка с одним владельцем успешно
- [x] Создание участка с несколькими владельцами (доли 1/2, 1/2) успешно
- [x] Валидация работает

---

### ✅ Фича 25: Frontend — Список владельцев (Owners)

**Цель:** Отобразить список владельцев с поиском.

**Файлы:**
- Создать: `frontend/src/views/OwnersView.vue`
- Создать: `frontend/src/stores/owners.ts`

**Шаги:**

- [x] Создать Pinia store `frontend/src/stores/owners.ts`:
  - `state: { owners: Owner[], loading: boolean }`
  - `actions: { fetchOwners(), searchOwners(query: string), createOwner(data) }`

- [x] Создать `frontend/src/views/OwnersView.vue`:
  - Таблица: имя, тип (физ/юр лицо), УНП, контакты
  - Поле поиска (по имени/УНП)
  - Кнопка "Добавить владельца" (для treasurer, admin)

- [x] Вызвать `fetchOwners` при монтировании

**Проверка:**
- [x] Открыть `/owners` — отображается таблица владельцев
- [x] Поиск по имени работает
- [x] Данные загружаются из API

---

### ✅ Фича 26: Frontend — Создание начисления (Accrual)

**Цель:** Реализовать форму создания начисления для финансового субъекта.

**Файлы:**
- Создать: `frontend/src/views/AccrualsView.vue`
- Создать: `frontend/src/views/AccrualCreateView.vue`
- Создать: `frontend/src/stores/accruals.ts`

**Шаги:**

- [x] Создать Pinia store `frontend/src/stores/accruals.ts`:
  - `state: { accruals: Accrual[] }`
  - `actions: { fetchAccruals(fsId: string), createAccrual(data), applyAccrual(id), cancelAccrual(id) }`

- [x] Создать `frontend/src/views/AccrualCreateView.vue`:
  - Выбор финансового субъекта (автокомплит с фильтром по СТ)
  - Выбор типа взноса (ContributionType)
  - Сумма (amount)
  - Дата начисления (accrual_date)
  - Период (period_start, period_end)
  - Кнопка "Создать начисление"

- [x] При сабмите вызвать `POST /api/v1/accruals/`

- [x] После создания — статус "created", требуется применить (кнопка "Применить")

- [x] Создать `frontend/src/views/AccrualsView.vue` — список начислений с фильтрами

**Проверка:**
- [x] Форма создания начисления работает
- [x] Начисление создаётся со статусом "created"
- [x] Кнопка "Применить" меняет статус на "applied"

---

### ✅ Фича 27: Frontend — Регистрация платежа (Payment)

**Цель:** Реализовать форму регистрации платежа.

**Файлы:**
- Создать: `frontend/src/views/PaymentsView.vue`
- Создать: `frontend/src/views/PaymentCreateView.vue`
- Создать: `frontend/src/stores/payments.ts`

**Шаги:**

- [x] Создать Pinia store `frontend/src/stores/payments.ts`:
  - `state: { payments: Payment[] }`
  - `actions: { fetchPayments(fsId: string), registerPayment(data), cancelPayment(id) }`

- [x] Создать `frontend/src/views/PaymentCreateView.vue`:
  - Выбор финансового субъекта (автокомплит)
  - Выбор плательщика (Owner, автокомплит)
  - Сумма (amount)
  - Дата платежа (payment_date)
  - Номер документа (опционально)
  - Описание (опционально)
  - Кнопка "Зарегистрировать платёж"

- [x] При сабмите вызвать `POST /api/v1/payments/`

- [x] После регистрации — статус "confirmed", баланс пересчитывается

- [x] Создать `frontend/src/views/PaymentsView.vue` — список платежей

**Проверка:**
- [x] Форма регистрации платежа работает
- [x] Платёж регистрируется со статусом "confirmed"
- [x] Баланс финансового субъекта обновляется

---

### ✅ Фича 28: Frontend — Отчёт по должникам

**Цель:** Отобразить отчёт по задолженностям.

**Файлы:**
- Создать: `frontend/src/views/ReportsView.vue`
- Создать: `frontend/src/views/DebtorsReportView.vue`
- Создать: `frontend/src/stores/reports.ts`

**Шаги:**

- [x] Создать Pinia store `frontend/src/stores/reports.ts`:
  - `state: { debtorsReport: DebtorInfo[], cashFlowReport: CashFlowReport | null }`
  - `actions: { fetchDebtorsReport(coopId: string, minDebt: number), fetchCashFlowReport(coopId, start, end) }`

- [x] Создать `frontend/src/views/DebtorsReportView.vue`:
  - Таблица: номер участка/счётчика, владелец, сумма долга
  - Фильтр: минимальная сумма долга
  - Сортировка по сумме долга (по убыванию)
  - Экспорт в CSV (опционально)

- [x] Вызвать `fetchDebtorsReport` при монтировании

**Проверка:**
- [x] Открыть `/reports/debtors` — отображается таблица должников
- [x] Фильтр по минимальной сумме работает
- [x] Данные корректны (соответствуют балансам)

---

### ✅ Фича 29: Frontend — Отчёт о движении средств

**Цель:** Отобразить отчёт о начислениях, платежах и расходах за период.

**Файлы:**
- Создать: `frontend/src/views/CashFlowReportView.vue`

**Шаги:**

- [x] Создать `frontend/src/views/CashFlowReportView.vue`:
  - Поля выбора периода: period_start, period_end
  - Кнопка "Сформировать отчёт"
  - Отображение:
    - Всего начислений за период
    - Всего платежей за период
    - Всего расходов за период
    - Чистый баланс (начисления - платежи - расходы)
  - Экспорт в PDF (опционально)

- [x] Вызвать `fetchCashFlowReport` при клике на кнопку

**Проверка:**
- [x] Выбор периода работает
- [x] Отчёт отображается корректно
- [x] Суммы соответствуют данным в БД

---

### ✅ Фича 30: Historization (django-simple-history для критичных сущностей)

**Цель:** Подключить историзацию изменений для PlotOwnership, Accrual, Payment, Expense.

**Файлы:**
- Изменить: `backend/requirements.txt` — добавить `django-simple-history` (или аналог для FastAPI)
- Изменить: `backend/app/models/plot_ownership.py`, `backend/app/models/accrual.py`, `backend/app/models/payment.py`, `backend/app/models/expense.py`
- Создать: `backend/alembic/versions/0009_add_history_tables.py`

**Шаги:**

**Примечание:** `django-simple-history` — это библиотека для Django. Для FastAPI можно использовать альтернативу или реализовать вручную через триггеры PostgreSQL или middleware.

**Альтернатива:** Использовать SQLAlchemy events для логирования изменений.

- [x] Исследовать решения для audit trail в FastAPI + SQLAlchemy:
  - Триггеры PostgreSQL с таблицами `*_history`
  - Библиотека `sqlalchemy-continuum` (если совместима с async)
  - Реализация через SQLAlchemy event listeners

- [x] Выбрать подход и реализовать для моделей:
  - `PlotOwnership`
  - `Accrual`
  - `Payment`
  - `Expense`

- [x] Создать миграцию для добавления history таблиц

- [x] Написать тест: изменение сущности → запись в history таблицу

**Проверка:**
- [x] При изменении PlotOwnership создаётся запись в history
- [x] При отмене Payment создаётся запись в history
- [x] Можно просмотреть историю изменений

---

### ✅ Фича 31: Seed данные и тестовые фикстуры

**Цель:** Создать скрипт для заполнения БД тестовыми данными.

**Файлы:**
- Создать: `backend/scripts/seed_db.py`
- Создать: `backend/tests/fixtures.py` — фикстуры для тестов

**Шаги:**

- [x] Создать `backend/scripts/seed_db.py`:
  - Создать 2 Cooperative (СТ "Ромашка", СТ "Василёк")
  - Создать 5 Owner (3 физ. лица, 2 юр. лица)
  - Создать 10 LandPlot с PlotOwnership (разные СТ)
  - Создать FinancialSubject для всех участков
  - Создать 3 ContributionType (Членский, Целевой, Электроэнергия)
  - Создать 3 ExpenseCategory (Дороги, Зарплата, Материалы)
  - Создать несколько Accrual и Payment
  - Создать несколько Expense
  - Создать 3 Meter с показаниями
  - Создать 3 AppUser (admin, chairman, treasurer)

- [x] Запуск: `python backend/scripts/seed_db.py`

- [x] Создать `backend/tests/fixtures.py` с pytest фикстурами для переиспользования в тестах:
  - `@pytest.fixture async def sample_cooperative(db: AsyncSession) -> Cooperative`
  - `@pytest.fixture async def sample_owner(db: AsyncSession) -> Owner`
  - и т.д.

**Проверка:**
- [x] `python backend/scripts/seed_db.py` — БД заполняется тестовыми данными
- [x] `psql -d controlling -c "SELECT COUNT(*) FROM land_plots"` — 10 участков
- [x] Фикстуры используются в тестах без дублирования кода

---

### ✅ Фича 32: Документация API (OpenAPI/Swagger)

**Цель:** Настроить автогенерацию документации API и добавить описания эндпоинтов.

**Файлы:**
- Изменить: `backend/app/main.py` — настроить OpenAPI schema
- Изменить: все роутеры — добавить docstrings и descriptions

**Шаги:**

- [x] Настроить OpenAPI в `backend/app/main.py`:
  - Установить title, version, description
  - Настроить tags для группировки эндпоинтов

- [x] Добавить описания ко всем эндпоинтам:
  - `summary` — краткое описание
  - `description` — детальное описание (что делает, параметры, ответы)
  - `response_model` — модель ответа

- [x] Добавить примеры ответов через `responses` parameter

**Проверка:**
- [x] Открыть http://127.0.0.1:8000/docs — отображается Swagger UI
- [x] Все эндпоинты сгруппированы по тегам (auth, cooperatives, land-plots и т.д.)
- [x] Описания и примеры корректны

---

### ✅ Фича 33: Деплой — Docker контейнеризация

**Цель:** Создать Docker образы для backend и frontend, docker-compose для локального запуска.

**Файлы:**
- Создать: `backend/Dockerfile`
- Создать: `frontend/Dockerfile`
- Создать: `docker-compose.yml`
- Создать: `.dockerignore`

**Шаги:**

- [x] Создать `backend/Dockerfile`:
  - Base image: `python:3.11-slim`
  - Установка зависимостей из `requirements.txt`
  - COPY исходников
  - CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

- [x] Создать `frontend/Dockerfile`:
  - Base image: `node:20-alpine`
  - Установка зависимостей: `pnpm install`
  - Build: `pnpm build`
  - Nginx для раздачи статики
  - COPY build в nginx

- [x] Создать `docker-compose.yml`:
  - Сервисы: `db` (PostgreSQL), `backend`, `frontend`
  - Volumes для персистентности БД
  - Networks для связи сервисов
  - Environment variables

- [x] Создать `.dockerignore` для исключения `venv`, `node_modules`, `.git`

**Проверка:**
- [x] `docker-compose up --build` — все сервисы запускаются
- [x] `curl http://localhost:8000/api/health` — backend работает
- [x] Открыть http://localhost — frontend работает
- [x] Frontend взаимодействует с backend через docker network

---

### ✅ Фича 34: CI/CD — GitHub Actions (тесты и линтеры)

**Цель:** Настроить автоматический запуск тестов и линтеров на каждый push.

**Файлы:**
- Создать: `.github/workflows/backend-tests.yml`
- Создать: `.github/workflows/frontend-tests.yml`
- Создать: `backend/.pre-commit-config.yaml` (опционально)

**Шаги:**

- [x] Создать `.github/workflows/backend-tests.yml`:
  - Trigger: on push и pull_request
  - Jobs: setup Python, install deps, run `pytest`, run `ruff check`

- [x] Создать `.github/workflows/frontend-tests.yml`:
  - Trigger: on push и pull_request
  - Jobs: setup Node, install deps, run `pnpm lint`, run `pnpm test` (Vitest)

- [x] Настроить линтеры:
  - Backend: `ruff` для форматирования и линтинга
  - Frontend: `eslint` + `prettier`

- [x] Добавить бейджи статуса в `README.md`

**Проверка:**
- [x] Push в репозиторий — запускаются GitHub Actions
- [x] Тесты проходят успешно
- [x] Линтеры не находят ошибок

---

### ✅ Фича 35: Финальная интеграция и E2E тесты

**Цель:** Протестировать полный флоу от frontend до backend.

**Файлы:**
- Создать: `e2e/test_full_flow.py` (Playwright или Selenium)
- Создать: `e2e/conftest.py`

**Шаги:**

- [x] Установить Playwright: `npm install -D @playwright/test`

- [x] Создать E2E тест `e2e/tests/test_full_flow.spec.ts`:
  - Сценарий 1: Логин → Создание участка → Создание начисления → Регистрация платежа → Проверка баланса
  - Сценарий 2: Логин → Просмотр отчёта по должникам → Проверка корректности данных

- [x] Запуск: `npm run test:e2e`

- [x] Проверить все критические пользовательские сценарии из дизайна

**Проверка:**
- [x] `npm run test:e2e` — E2E тесты проходят
- [x] Все критические флоу работают корректно

---

## Итог

После выполнения всех фич у тебя будет:

- ✅ Полнофункциональный бэкенд на FastAPI с PostgreSQL
- ✅ Модели данных для всех сущностей (Cooperative, Owner, LandPlot, FinancialSubject, Accrual, Payment, Expense, Meter)
- ✅ JWT аутентификация с ролями (admin, chairman, treasurer)
- ✅ CRUD API для всех сущностей с разграничением доступа
- ✅ Расчёт балансов и финансовая аналитика
- ✅ Фронтенд на Vue 3 с TypeScript и Pinia
- ✅ Формы для создания участков, начислений, платежей
- ✅ Отчёты по должникам и движению средств
- ✅ Тесты (unit, integration, E2E)
- ✅ Docker контейнеризация
- ✅ CI/CD через GitHub Actions

**Следующий шаг:** Начни с **Фичи 1** и двигайся последовательно. Каждая фича — это одна сессия работы с чёткими шагами и проверкой.

Удачи! 🚀
