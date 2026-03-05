# Спецификация реализации: Ledger-ready MVP (временная модель и необратимость)

**Назначение:** Пошаговое техническое задание для агента **backend-developer**. Все изменения — в границах backend, без смешения слоёв Clean Architecture.  
**Контекст:** ADR 0002 (`docs/architecture/adr/0002-financial-temporal-and-ledger-ready.md`), анализ `docs/plan/financial-architecture-analysis.md`.  
**Проверка:** После каждого этапа — тесты проходят, ruff чист, слои не смешаны (API не импортирует Infrastructure; Domain не импортирует FastAPI/SQLAlchemy; Application использует только Domain + DTOs).

---

## Передача агенту

- **Агент:** **backend-developer** (`.cursor/rules/agents/backend-developer.mdc`). Задание: «Реализуй по шагам спецификацию из `docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`. Этапы выполняй строго по порядку (1 → 2 → … → 5). После каждого этапа запускай pytest и ruff. Не смешивай слои.»
- **Порядок:** Не переходить к этапу N+1, пока не принят этап N и не проходят тесты.

---

## Кто выполняет

- **Роль:** **backend-developer** (см. `.cursor/rules/agents/backend-developer.mdc`).
- **Не делать:** изменения в `docs/architecture/glossary/` (только Lead Architect); создание/правка ADR по содержанию — только после согласования. Реализатор может обновлять индекс ADR (добавить строку в README) после принятия решения.
- **Правило слоёв:**
  - **Domain:** только чистый Python (entities, repository interfaces, domain services, domain events). Без импортов из `app.modules.*.infrastructure`, `app.modules.*.api`, FastAPI, SQLAlchemy, Pydantic (кроме если используется только для типов в type hints без рантайм-зависимости).
  - **Application:** use cases, DTOs (Pydantic). Импортирует Domain (entities, repository interfaces). Не импортирует Infrastructure или API.
  - **Infrastructure:** ORM-модели, реализации репозиториев. Импортирует Domain (entities, interfaces). Не импортирует Application или API.
  - **API:** routes, schemas (реэкспорт или тонкие обёртки над DTOs). Импортирует Application (use cases, DTOs) и deps. Не импортирует Infrastructure или Domain entities напрямую (типы для ответов — через DTOs/schemas).

---

## Этап 1: Модель данных — новые поля (Accrual, Payment, Expense)

**Цель:** Добавить во все финансовые операции поля `cancelled_at`, `cancelled_by_user_id`, `cancellation_reason`, `operation_number`. Убедиться, что `created_at` трактуется как NOT NULL (в миграции и в ORM).

### 1.1. Миграция Alembic

- **Файл:** новый файл в `backend/alembic/versions/`, имя вида `0010_add_financial_operation_audit_fields.py` (или следующий номер по порядку).
- **Действия:**
  - Добавить столбцы в таблицы `accruals`, `payments`, `expenses`:
    - `cancelled_at` — `sa.DateTime(timezone=True)`, `nullable=True`
    - `cancelled_by_user_id` — `Guid()` (из `app.db.base`) или `sa.CHAR(36)` для SQLite-совместимости; FK на `app_users.id` опционально (если уже есть FK-политика); `nullable=True`
    - `cancellation_reason` — `sa.Text()`, `nullable=True`
    - `operation_number` — `sa.String(50)` или достаточная длина, `nullable=False` после backfill (см. ниже)
  - Для существующих строк в `accruals`, `payments`, `expenses`: задать `operation_number` уникальным значением (например, `'{table_short}_{id}'` или `gen_random_uuid()` в сыром SQL для старых записей), затем `ALTER COLUMN operation_number SET NOT NULL`.
  - Добавить `UniqueConstraint` на `operation_number` в рамках таблицы (или в миграции `op.create_unique_constraint`).
  - Добавить те же столбцы в таблицы истории: `accruals_history`, `payments_history`, `expenses_history` (nullable для старых записей).
- **Не делать:** не менять существующие миграции кроме текущей новой; не удалять поля.

### 1.2. ORM-модели (Infrastructure)

- **Файлы:**
  - `backend/app/modules/accruals/infrastructure/models.py`
  - `backend/app/modules/payments/infrastructure/models.py`
  - `backend/app/modules/expenses/infrastructure/models.py`
- **Действия для каждой модели (AccrualModel, PaymentModel, ExpenseModel):**
  - Добавить атрибуты:
    - `cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)`
    - `cancelled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Guid(), ForeignKey("app_users.id"), nullable=True)` (или без FK при необходимости)
    - `cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)`
    - `operation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)` (после миграции с backfill)
  - В `to_domain()` и `from_domain()` передавать/принимать эти поля в доменную сущность.
- **История:** в `AccrualHistoryModel`, `PaymentHistoryModel`, `ExpenseHistoryModel` добавить те же четыре столбца (nullable), чтобы снимки при update/delete их содержали.
- **Не делать:** не добавлять бизнес-логику в модели; не импортировать Application/Domain use cases.

### 1.3. Domain-сущности (Domain)

- **Файлы:**
  - `backend/app/modules/accruals/domain/entities.py`
  - `backend/app/modules/payments/domain/entities.py`
  - `backend/app/modules/expenses/domain/entities.py`
- **Действия:** В dataclass `Accrual`, `Payment`, `Expense` добавить поля:
  - `cancelled_at: datetime | None = None`
  - `cancelled_by_user_id: UUID | None = None`
  - `cancellation_reason: str | None = None`
  - `operation_number: str` (обязательное; для существующих сущностей при загрузке из БД будет заполнено миграцией).
- **Не делать:** не добавлять методы cancel здесь (это Этап 3); не менять другие доменные сущности (ContributionType, ExpenseCategory и т.д.) кроме перечисленных.

### 1.4. Application DTOs и API-схемы

- **Файлы:**
  - `backend/app/modules/accruals/application/dtos.py`
  - `backend/app/modules/payments/application/dtos.py`
  - `backend/app/modules/expenses/application/dtos.py`
- **Действия:** В DTO «in DB» (AccrualInDB, PaymentInDB, ExpenseInDB или аналог) добавить поля:
  - `cancelled_at: datetime | None = None`
  - `cancelled_by_user_id: UUID | None = None`
  - `cancellation_reason: str | None = None`
  - `operation_number: str`
- **API:** В ответах роутов (где формируется объект из entity) передавать эти поля в схему ответа. Файлы маршрутов: `backend/app/modules/accruals/api/routes.py`, `backend/app/modules/payments/api/routes.py`, `backend/app/modules/expenses/api/routes.py` — везде, где возвращается одна сущность или список (GET, POST create, POST cancel, и т.д.), добавить в конструктор ответа поля `cancelled_at`, `cancelled_by_user_id`, `cancellation_reason`, `operation_number`.
- **Не делать:** не добавлять в Create-схемы поле `operation_number` от клиента — оно задаётся на бэкенде.

### 1.5. Репозитории (Infrastructure) — маппинг при update

- **Файлы:**
  - `backend/app/modules/accruals/infrastructure/repositories.py`
  - `backend/app/modules/payments/infrastructure/repositories.py`
  - `backend/app/modules/expenses/infrastructure/repositories.py`
- **Действия:** В методе `update()` при присвоении полей из entity в model добавить присвоение `cancelled_at`, `cancelled_by_user_id`, `cancellation_reason`. Поле `operation_number` при update не менять (оно задаётся при создании).
- **Не делать:** не менять логику get/add/delete.

### 1.6. Генерация operation_number при создании

- **Где:** Application layer — use case создания платежа/начисления/расхода.
- **Файлы:**
  - `backend/app/modules/payments/application/use_cases.py` (RegisterPaymentUseCase)
  - `backend/app/modules/accruals/application/use_cases.py` (CreateAccrualUseCase, MassCreateAccrualsUseCase)
  - `backend/app/modules/expenses/application/use_cases.py` (CreateExpenseUseCase)
- **Логика:** Перед вызовом `repo.add(entity)` сформировать `operation_number`. Формат — на выбор, но уникальный и человекочитаемый, например: `PAY-{cooperative_id_short}-{year}-{sequence}` или `ACC-...`, `EXP-...`. Последовательность можно брать из `max(operation_number)` по префиксу за год или из отдельной таблицы-счётчика (простой вариант — UUID короткий или timestamp + random). Важно: гарантировать уникальность в рамках таблицы (unique constraint уже в БД).
- **Откуда брать cooperative_id:** для Payment/Accrual — через financial_subject_id (нужен запрос к FinancialSubjectRepository или передача cooperative_id в use case); для Expense — уже есть в сущности.
- **Не делать:** не генерировать operation_number в Domain entity (это прикладная политика нумерации); не писать сложную распределённую нумерацию без требования.

### 1.7. History events — новые столбцы в снимке

- **Файл:** `backend/app/db/history_events.py`
- **Действия:** В списках `snapshot_columns` для Accrual, Payment, Expense добавить: `"cancelled_at"`, `"cancelled_by_user_id"`, `"cancellation_reason"`, `"operation_number"`.
- **Не делать:** не менять логику слушателей.

### 1.8. Seed и фикстуры

- **Файлы:** `backend/app/scripts/seed_db.py`, `backend/tests/fixtures.py` (если там создаются Accrual, Payment, Expense).
- **Действия:** При создании экземпляров Accrual, Payment, Expense задавать `operation_number` (уникальный в рамках скрипта/фикстуры, например `ACC-TEST-1`, `PAY-TEST-1`, `EXP-TEST-1` или с суффиксом id).
- **Не делать:** не ломать идемпотентность seed_db.

### 1.9. Тесты (Этап 1)

- **Модели:** В `backend/tests/test_models/test_accrual.py`, `test_payment.py`, `test_expense.py` добавить тесты:
  - что при создании модели можно задать и прочитать `cancelled_at`, `cancelled_by_user_id`, `cancellation_reason`, `operation_number`;
  - что после миграции и создания сущности эти поля сохраняются и загружаются.
- **API:** В `backend/tests/test_api/test_accruals.py`, `test_payments.py`, `test_expenses.py` обновить существующие тесты: в ответах ожидать наличие полей `operation_number`, `cancelled_at`, `cancelled_by_user_id`, `cancellation_reason` (где применимо); при отмене проверять, что в ответе после cancel появляются заполненные cancelled_* (после Этапа 3).
- **Репозитории:** При необходимости добавить тест в `tests/test_models/` или `tests/test_services/`, что update сохраняет cancelled_at/cancelled_by_user_id/cancellation_reason.

**Критерий приёмки Этапа 1:** Миграция применяется без ошибок; все текущие тесты проходят; новые поля присутствуют в ORM, домене, DTO и API-ответах; operation_number выставляется при создании и не меняется при update.

---

## Этап 2: Правило баланса на дату и контракт as_of_date

**Цель:** Единое правило участия операции в балансе на дату X; контракт `calculate_balance(financial_subject_id, as_of_date=None)`; реализация в одном месте (BalanceRepository + при необходимости доменный сервис).

### 2.1. Правило участия в балансе (формализация)

- **Операция участвует в балансе на дату X (date), если и только если:**
  - event_date ≤ X (для Accrual — `accrual_date`, для Payment — `payment_date`);
  - date(created_at) ≤ X (сравнение по дате без времени);
  - для Accrual: status == 'applied'; для Payment: status == 'confirmed';
  - **и** операция «не отменена на дату X»: (status != 'cancelled') ИЛИ (cancelled_at не NULL и date(cancelled_at) > X).  
  То есть отменённая операция входит в баланс на дату X только если отмена произошла после X (cancelled_at > X).
- Итог: в выборку для сумм попадают только операции, прошедшие все четыре условия.

### 2.2. Интерфейс репозитория баланса (Domain)

- **Файл:** `backend/app/modules/financial_core/domain/repositories.py`
- **Действия:** В `IBalanceRepository` изменить сигнатуру:
  - `async def calculate_balance(self, financial_subject_id: UUID, as_of_date: date | None = None) -> Balance | None`
  - Добавить в docstring: при `as_of_date=None` — баланс «на сейчас» (все операции, подходящие по правилу на «текущую дату» или без отсечки по дате — оставить единообразие: трактовать None как «на конец сегодня» по часовому поясу сервера или UTC).
- **Не делать:** не добавлять зависимости от Infrastructure в интерфейс.

### 2.3. Реализация в BalanceRepository (Infrastructure)

- **Файл:** `backend/app/modules/financial_core/infrastructure/repositories.py`
- **Действия:**
  - В `calculate_balance(self, financial_subject_id, as_of_date=None)`:
    - Если `as_of_date` не задан — принять `as_of_date = date.today()` (UTC или серверный часовой пояс — единообразно в проекте).
    - Сумма начислений: Accrual где `financial_subject_id == id`, `status == 'applied'`, `accrual_date <= as_of_date`, `func.date(Accrual.created_at) <= as_of_date`, и участие на дату: `(Accrual.status != 'cancelled') OR (Accrual.cancelled_at.isnot(None) & (func.date(Accrual.cancelled_at) > as_of_date))` (в SQL: status <> 'cancelled' OR (cancelled_at IS NOT NULL AND DATE(cancelled_at) > :as_of_date)). Аналогично для Payment: `status == 'confirmed'`, `payment_date <= as_of_date`, `created_at` по дате ≤ as_of_date, и то же условие по cancelled_at.
    - Использовать `func.sum(Accrual.amount)` и `func.sum(Payment.amount)` с указанными фильтрами.
  - В `get_balances_by_cooperative(self, cooperative_id, as_of_date=None)` добавить параметр `as_of_date` и применять то же правило при агрегации по субъектам.
- **Не делать:** не дублировать правило в контроллере; не считать баланс в других модулях напрямую через сырой SQL без использования этого репозитория.

### 2.4. Domain-сервис BalanceCalculator (Domain)

- **Файл:** `backend/app/modules/financial_core/domain/services.py`
- **Действия:** Оставить текущий метод `calculate(total_accruals, total_payments)` без изменений (он уже есть). Опционально: добавить в docstring отсылку к правилу участия операций на дату (что отбор операций выполняет репозиторий, сервис только считает разность).
- **Не делать:** не передавать в BalanceCalculator дату или сессию БД — он остаётся чистым доменным сервисом.

### 2.5. Use cases (Application)

- **Файл:** `backend/app/modules/financial_core/application/use_cases.py`
- **Действия:**
  - `GetBalanceUseCase.execute(self, financial_subject_id: UUID, as_of_date: date | None = None)` — передавать `as_of_date` в `self.balance_repo.calculate_balance(financial_subject_id, as_of_date)`.
  - `GetBalancesByCooperativeUseCase.execute(self, cooperative_id: UUID, as_of_date: date | None = None)` — передавать `as_of_date` в репозиторий.
- **Не делать:** не менять тип возвращаемого значения (Balance или dict — как сейчас); Balance — доменная сущность, её возвращает репозиторий.

### 2.6. API (financial_core)

- **Файл:** `backend/app/modules/financial_core/api/routes.py`
- **Действия:**
  - В эндпоинте `GET /{subject_id}/balance` добавить query-параметр `as_of_date: date | None = Query(None, description="Баланс на дату (по умолчанию — текущая)")`.
  - Передавать его в `get_balance_use_case.execute(financial_subject_id=subject_id, as_of_date=as_of_date)`.
  - В эндпоинте `GET /balances` добавить такой же query-параметр и передавать в use case.
- **Не делать:** не менять формат ответа (BalanceInfo остаётся тем же).

### 2.7. Тесты (Этап 2)

- **Репозиторий/сервис баланса:** В `backend/tests/test_api/test_financial_subjects.py` (или отдельный файл для баланса, если появится):
  - Тест: баланс на дату X: создать начисления и платежи с разными accrual_date/payment_date и created_at; отменить один платёж с cancelled_at = X+1 день; запросить баланс на X — отменённый платёж должен входить; запросить баланс на X+2 — не должен входить.
  - Тест: при as_of_date=None возвращается баланс на «сегодня».
- **API:** Тест GET `/{subject_id}/balance?as_of_date=2025-01-15` с ожидаемым результатом по заранее созданным данным.

**Критерий приёмки Этапа 2:** Контракт с `as_of_date` реализован в интерфейсе, репозитории, use case и API; правило участия на дату соблюдено в одном месте (репозиторий); тесты на баланс на дату проходят.

---

## Этап 3: Отмена в домене (Rich Domain) и API cancel с причиной/пользователем

**Цель:** Метод `cancel(cancelled_by, reason, now)` в сущностях Payment, Accrual, Expense; use case только вызывает его и сохраняет; API принимает опционально reason и передаёт current_user.id как cancelled_by.

### 3.1. Domain-сущности — метод cancel

- **Файлы:**
  - `backend/app/modules/payments/domain/entities.py`
  - `backend/app/modules/accruals/domain/entities.py`
  - `backend/app/modules/expenses/domain/entities.py`
- **Действия:** В классе Payment (Accrual, Expense) добавить метод:
  - `def cancel(self, cancelled_by: UUID, reason: str | None, now: datetime) -> None`
  - Внутри: если `self.status == "cancelled"` (для Payment/Expense) или `self.status == "cancelled"` (для Accrual), выбросить доменное исключение (например из `app.modules.shared.kernel.exceptions` — DomainError или использовать ValidationError, если так принято в проекте).
  - Иначе: установить `self.status = "cancelled"`, `self.cancelled_at = now`, `self.cancelled_by_user_id = cancelled_by`, `self.cancellation_reason = reason or None`.
- **Не делать:** не обращаться к БД или репозиторию из сущности; не импортировать FastAPI/SQLAlchemy.

### 3.2. Use cases отмены (Application)

- **Файлы:**
  - `backend/app/modules/payments/application/use_cases.py` — CancelPaymentUseCase
  - `backend/app/modules/accruals/application/use_cases.py` — CancelAccrualUseCase
  - `backend/app/modules/expenses/application/use_cases.py` — CancelExpenseUseCase
- **Действия:** Изменить сигнатуру `execute`:
  - Добавить аргументы: `cancelled_by_user_id: UUID`, `cancellation_reason: str | None = None`, `cancelled_at: datetime | None = None` (если None — подставлять datetime.now(UTC)).
  - Внутри: загрузить сущность через repo; вызвать `entity.cancel(cancelled_by_user_id, cancellation_reason, cancelled_at or now)`; затем `return await self.repo.update(entity)`.
  - Удалить прямое присвоение `entity.status = "cancelled"` из use case.
- **Не делать:** не оставлять дублирование логики отмены в use case; не вызывать repository из domain entity.

### 3.3. API cancel — передача пользователя и причины

- **Файлы:**
  - `backend/app/modules/payments/api/routes.py` — эндпоинт POST `/{payment_id}/cancel`
  - `backend/app/modules/accruals/api/routes.py` — эндпоинт POST `/{accrual_id}/cancel`
  - `backend/app/modules/expenses/api/routes.py` — эндпоинт POST `/{expense_id}/cancel`
- **Действия:**
  - Добавить в эндпоинт cancel зависимость `current_user: Annotated[AppUser, Depends(require_role(...))]`.
  - Добавить тело запроса (Pydantic) опционально: `CancelBody(reason: str | None = None)` или query-параметр `reason: str | None = None`.
  - Вызов use case: `execute(..., cancelled_by_user_id=current_user.id, cancellation_reason=reason)` (и при необходимости cancelled_at из datetime.now(UTC)).
- **Не делать:** не передавать в use case объект AppUser целиком, только id (UUID).

### 3.4. Тесты (Этап 3)

- **Домен:** В `backend/tests/test_models/` или в отдельном `test_domain/` (если есть) добавить тесты для entity.cancel():
  - вызов cancel первый раз — статус и поля cancelled_* устанавливаются;
  - повторный вызов cancel — исключение (already cancelled).
- **API:** В test_api для accruals, payments, expenses: тест cancel с передачей reason; тест что в ответе после cancel присутствуют cancelled_at, cancelled_by_user_id, cancellation_reason; тест cancel уже отменённого — 400 с сообщением.

**Критерий приёмки Этапа 3:** Отмена выполняется только через entity.cancel(); use case не меняет статус напрямую; API передаёт пользователя и причину; тесты покрывают домен и API.

---

## Этап 4: Защита amount (immutability)

**Цель:** После создания операции amount не изменять: в репозитории при update не обновлять поле amount; в домене не предоставлять setter (оставить dataclass с полем amount — без присвоения извне после создания в use case не трогать amount).

### 4.1. Репозитории update (Infrastructure)

- **Файлы:** `backend/app/modules/accruals/infrastructure/repositories.py`, `backend/app/modules/payments/infrastructure/repositories.py`, `backend/app/modules/expenses/infrastructure/repositories.py`
- **Действия:** В методе `update()` не присваивать `model.amount = entity.amount` (удалить эту строку). Остальные поля (status, cancelled_at, document_number, description и т.д.) — по-прежнему обновлять по entity.
- **Не делать:** не добавлять проверки в репозитории на «если amount изменился — выбросить» (достаточно не обновлять).

### 4.2. Use cases обновления (Application)

- **Файлы:** Если есть UpdatePaymentUseCase / UpdateAccrualUseCase (или аналог) — убедиться, что они не устанавливают amount из ввода пользователя. В DTO Update не должно быть поля amount (или оно игнорируется при применении к entity для update). Проверить `backend/app/modules/payments/application/use_cases.py`, accruals, expenses — при наличии update use case не передавать amount в entity при обновлении.
- **Не делать:** не удалять возможность обновлять document_number, description и т.д., если это есть по контракту.

### 4.3. Тесты (Этап 4)

- Тест: после update entity с другим amount сохранённая в БД сумма не изменилась (репозиторий или API PATCH не меняет amount).

**Критерий приёмки Этапа 4:** В репозиториях при update amount не записывается; тест подтверждает неизменность amount после update.

---

## Этап 5: Domain Events (заготовка)

**Цель:** Определить типы событий PaymentConfirmed, PaymentCancelled, AccrualApplied, AccrualCancelled; вызывать их при соответствующих действиях; пока только логирование или хранение в памяти (не персистить в БД).

### 5.1. События в домене (Domain)

- **Файл:** можно в `backend/app/modules/payments/domain/events.py` и `backend/app/modules/accruals/domain/events.py` (или один общий модуль событий финансов, если принято в проекте).
- **Действия:** Объявить dataclass-события, например:
  - `PaymentConfirmed(payment_id: UUID, financial_subject_id: UUID, amount: Decimal, payment_date: date, ...)`
  - `PaymentCancelled(payment_id: UUID, cancelled_at: datetime, cancelled_by: UUID, reason: str | None)`
  - `AccrualApplied(accrual_id: UUID, financial_subject_id: UUID, amount: Decimal, accrual_date: date, ...)`
  - `AccrualCancelled(accrual_id: UUID, cancelled_at: datetime, cancelled_by: UUID, reason: str | None)`
- Наследование от базового типа события (если есть в `app.modules.shared.kernel.events`) — по принятому в проекте.
- **Не делать:** не импортировать Application или Infrastructure.

### 5.2. Публикация в use cases (Application)

- **Файлы:** RegisterPaymentUseCase — после успешного add вызвать event_dispatcher.dispatch(PaymentConfirmed(...)). CancelPaymentUseCase — после entity.cancel() и repo.update() вызвать dispatch(PaymentCancelled(...)). Аналогично для Accrual: ApplyAccrualUseCase — dispatch(AccrualApplied(...)); CancelAccrualUseCase — dispatch(AccrualCancelled(...)).
- **Зависимости:** CancelPaymentUseCase и RegisterPaymentUseCase должны получать event_dispatcher (из deps); то же для accruals. Добавить в `app.modules.deps.py` передачу event_dispatcher в эти use cases, если его ещё нет.
- **Не делать:** не сохранять события в БД в этом этапе; не блокировать ответ API на обработку событий (если обработчик синхронный и быстрый — можно вызывать синхронно).

### 5.3. Обработчик (логирование)

- **Файл:** например `backend/app/modules/financial_core/application/event_handlers.py` или в существующем месте регистрации обработчиков.
- **Действия:** Подписать обработчик на PaymentConfirmed, PaymentCancelled, AccrualApplied, AccrualCancelled — логировать (logging.info) факт события и минимальный контекст (id, amount, date). Регистрация обработчика — там же, где регистрируется event_dispatcher (main или deps).
- **Не делать:** не писать в БД, не вызывать внешние API.

### 5.4. Тесты (Этап 5)

- Тест: после регистрации платежа (и после отмены) в тестовом диспетчере событий зафиксировано соответствующее событие (mock или in-memory список событий).
- Аналогично для Accrual apply/cancel.

**Критерий приёмки Этапа 5:** События объявлены в Domain; use cases их диспатчат; хотя бы один обработчик логирует; тесты проверяют факт диспатча.

---

## Этап 6: Финансовый API — опциональный query as_of_date (итоговая проверка)

Уже включено в Этап 2 (API financial_core). Здесь — только напоминание: в `GET /financial-subjects/balances` и `GET /financial-subjects/{id}/balance` параметр `as_of_date` должен быть опциональным и передаваться в use case.

---

## Порядок выполнения и проверки

1. Выполнять этапы строго по порядку: 1 → 2 → 3 → 4 → 5.
2. После каждого этапа: запуск `pytest` из `backend/`; запуск `ruff check .` и `ruff format --check .`; убедиться, что нет импортов API из Infrastructure и Domain из Application/Infrastructure.
3. Перед коммитом: обновить список изменённых файлов в описании PR; при необходимости обновить `docs/development-index.md` (если добавлена новая задача или ссылка на ADR).

---

## Файлы, которые не менять (границы ответственности)

- `docs/architecture/glossary/*` — только Lead Architect.
- Содержимое ADR 0002 по смыслу решений (можно править опечатки или ссылки по согласованию).
- Frontend — вне скоупа этой спецификации.
- `app/db/base.py`, `app/db/session.py` — без необходимости не менять; при добавлении новых полей в модели миграции генерируются через Alembic.

---

## Краткий чек-лист по слоям (самопроверка агента)

- [ ] Domain: нет импортов из app.modules.*.infrastructure, app.modules.*.api, sqlalchemy, fastapi.
- [ ] Application: импортирует только domain (entities, repositories interfaces, events), shared kernel, pydantic для DTOs.
- [ ] Infrastructure: импортирует domain (entities, interfaces) и ORM-модели; не импортирует application use cases или api.
- [ ] API: импортирует application (use cases, DTOs), deps; не импортирует infrastructure или domain entities (типы ответов — через DTOs/schemas).
