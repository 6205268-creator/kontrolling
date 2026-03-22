# Финансовая модель — итог реализации (фазы 1–5)

**Обновлено:** 2026-03-22  
**Статус:** План [`INDEX.md`](INDEX.md) реализован по фазам 1–5.  
**Ранние коммиты (фазы 1–3):** `main` — `7478ba8`, `463c0ee`, `65b265f`. Фазы 4–5: связанный код в репозитории (см. ниже).

---

## Краткое резюме

Реализована **устойчивая финансовая модель** для учёта СТ: Clean Architecture, Money VO, распределение платежей, **финансовые периоды и снимки баланса**, **строки долга и пени**, отчёты (оборотная ведомость, должники).

**Проверка качества:** из каталога `backend` — `pytest`, `ruff check`, `ruff format --check`. Точное число тестов не фиксируется в документе (растёт с фичами). Схема БД — из ORM при старте приложения, без Alembic.

---

## Фаза 1: Фундамент

**Коммит:** `7478ba8`  
**Ветка:** `feature/fin-model-phase-1`

### Что сделано

| Задача | Результат |
|--------|-----------|
| **1.1 due_date** | Поле `due_date` на Accrual, ORM/API, тесты |
| **1.2 Правило баланса** | Исправлен фильтр по `created_at` (ADR 0002) |
| **1.3 Money VO** | `shared/kernel/money.py`, 27 тестов |

### Файлы

- `backend/app/modules/shared/kernel/money.py` — Money Value Object
- `backend/tests/test_core/test_money.py`
- `backend/tests/test_api/test_accruals.py` (3 новых теста)

### Ключевые изменения

```python
# Money VO — типовая безопасность
@dataclass(frozen=True)
class Money:
    amount: Decimal
    CURRENCY = "BYN"
    PRECISION = Decimal("0.01")
    
    def __add__(self, other: "Money") -> "Money": ...
    def rounded(self) -> "Money": ...
    def is_zero(self) -> bool: ...
```

---

## Фаза 2: Архитектура баланса

**Коммит:** `463c0ee`  
**Ветка:** `feature/fin-model-phase-2`

### Что сделано

| Задача | Результат |
|--------|-----------|
| **2.1 Specification Pattern** | `BalanceParticipationRule` + SQL translator |
| **2.2 Агрегатные провайдеры** | Устранена зависимость BalanceRepository от чужих моделей |
| **2.3 ADR 0004** | CQRS для баланса (snapshots) — документ |

### Файлы

- `backend/app/modules/financial_core/domain/balance_spec.py`
- `backend/app/modules/financial_core/infrastructure/balance_spec_sql.py`
- `backend/app/modules/financial_core/domain/repositories.py` (интерфейсы)
- `backend/app/modules/accruals/infrastructure/repositories.py` (AccrualAggregateProvider)
- `backend/app/modules/payments/infrastructure/repositories.py` (PaymentAggregateProvider)
- `backend/tests/test_core/test_balance_spec.py` (21 тест)
- `backend/tests/test_core/test_balance_spec_sql_consistency.py` (2 теста)
- `docs/architecture/adr/0004-balance-cqrs-snapshots.md`

### Ключевые изменения

```python
# BalanceParticipationRule — доменное правило
@dataclass(frozen=True)
class BalanceParticipationRule:
    as_of_date: date
    
    def accrual_participates(...) -> bool:
        # 1. accrual_date <= as_of_date
        # 2. created_at <= as_of_date
        # 3. status == 'applied' OR (cancelled AND cancelled_at > as_of_date)

# BalanceRepository — без прямых импортов AccrualModel/PaymentModel
class BalanceRepository:
    def __init__(self, session, accrual_provider, payment_provider):
        self.accrual_provider = accrual_provider  # IAccrualAggregateProvider
        self.payment_provider = payment_provider  # IPaymentAggregateProvider
```

---

## Фаза 3: Распределение платежей

**Коммит:** `65b265f`  
**Ветка:** `feature/fin-model-phase-3`

### Что сделано

| Задача | Результат |
|--------|-----------|
| **3.1 Ревизия модели** | Member — тонкая сущность, MemberPlot удалён |
| **3.2 PersonalAccount** | Лицевой счёт + транзакции, use cases |
| **3.3 PaymentDistribution** | Распределение по приоритетам |
| **3.4 Интеграция** | PaymentConfirmedHandler — авто-зачисление |
| **3.5 API** | 4 endpoints для баланса и истории |

### Файлы

- `backend/app/modules/payment_distribution/domain/entities.py` (Member, PersonalAccount, PaymentDistribution)
- `backend/app/modules/payment_distribution/domain/repositories.py` (интерфейсы)
- `backend/app/modules/payment_distribution/domain/events.py` (события)
- `backend/app/modules/payment_distribution/infrastructure/models.py` (ORM)
- `backend/app/modules/payment_distribution/infrastructure/repositories.py` (репозитории)
- `backend/app/modules/payment_distribution/infrastructure/event_handlers.py` (PaymentConfirmedHandler)
- `backend/app/modules/payment_distribution/application/use_cases.py`
- `backend/app/modules/payment_distribution/application/dtos.py`
- `backend/app/modules/payment_distribution/api/routes.py`
- `backend/app/modules/payment_distribution/tests/test_use_cases.py` (3 теста)
- `docs/data-model/payment-distribution-erd.md` (обновлена)

### Ключевые изменения

```python
# Member — тонкая сущность
@dataclass
class Member:
    owner_id: UUID
    cooperative_id: UUID
    personal_account_id: UUID | None
    status: str  # active, closed

# PersonalAccount — лицевой счёт
@dataclass
class PersonalAccount:
    member_id: UUID
    account_number: str
    balance: Money  # положительный = аванс
    
    def credit(self, amount: Money): ...
    def debit(self, amount: Money): ...

# PaymentConfirmedHandler — автоматическое распределение
class PaymentConfirmedHandler:
    async def __call__(self, event):
        # 1. Get/create member
        # 2. Credit account
        # 3. Distribute by priority
```

---

## Фаза 4: Финансовые периоды и отчётность

**Закрыта:** 2026-03-22.

| Направление | Реализация (ориентиры) |
|-------------|-------------------------|
| Периоды | `FinancialPeriod`, репозитории, API в `financial_core` |
| Окно переоткрытия | `cooperatives.period_reopen_allowed_days` |
| Блокировка операций | `PeriodOperationGuard`, `period_auto_lock`; интеграция в начисления и платежи |
| Снимки | `BalanceSnapshot` при закрытии периода; чтение баланса из snapshot в закрытом периоде |
| Оборотка | `GetTurnoverSheetUseCase`, `GET /api/reports/turnover` |
| Тесты | `backend/tests/test_api/test_financial_periods_phase4.py` |

**Оговорка:** частичный unique для `financial_periods` задаётся в ORM — см. [`docs/plan/current-focus.md`](../current-focus.md) (блок «Не дублировать: Фаза 4»).

---

## Фаза 5: Долги и пени

**Закрыта:** 2026-03-22.

| Направление | Реализация (ориентиры) |
|-------------|-------------------------|
| Долг | `DebtLine`, обработчики событий начислений и распределения платежей |
| Пени | `PenaltyCalculator`, стратегия, `AccruePenaltiesUseCase`, API `/api/penalties` |
| Планировщик | `app/scheduler.py` — автоначисление пеней по расписанию кооператива |
| Отчёт | `GET /api/reports/debtors`, тесты в `backend/tests/test_api/test_reports.py` |

Критерии приёмки и детали: [`phase-5-debt-penalties.md`](phase-5-debt-penalties.md).

---

## Архитектурные улучшения

### 1. Clean Architecture

**Было:**
```
financial_core/infrastructure → accruals/infrastructure/models (нарушение!)
```

**Стало:**
```
financial_core/infrastructure → IAccrualAggregateProvider (интерфейс)
                              → AccrualAggregateProvider (реализация в accruals)
```

### 2. Specification Pattern

**Было:** Логика правила в SQL-запросах BalanceRepository  
**Стало:** 
- `BalanceParticipationRule` (domain) — чистая логика
- `BalanceParticipationSqlFilter` (infrastructure) — трансляция в SQL
- Тестируется отдельно, без БД

### 3. Money Value Object

**Было:** `Decimal` без обёртки  
**Стало:** 
- Типовая безопасность (нельзя сложить сумму и не-сумму)
- Единое округление (2 знака для BYN)
- Методы `is_zero`, `is_positive`, `rounded()`

### 4. Event-driven архитектура

**Было:** Платёж просто создавался  
**Стало:**
```
PaymentConfirmed → PaymentConfirmedHandler
                 → CreditAccountUseCase (зачисление)
                 → DistributePaymentUseCase (распределение)
```

---

## Вне объёма фаз 1–5 (идеи / пост-MVP)

Не входили в закрытие плана [`INDEX.md`](INDEX.md) как обязательные критерии фаз:

- Отчёт **«Движение денежных средств»** (отдельный регламентированный отчёт).
- **PaymentDistributionRule** как настраиваемые приоритеты распределения (UI/конфиг).
- **Требования об оплате / уведомления** (notification).
- Импорт и сверка **банковских выписок** — отдельный контур от сценария «год жизни СТ» (см. [`docs/plan/current-focus.md`](../current-focus.md)).

---

## Как использовать

### 1. Зачисление платежа (автоматическое)

```python
# При создании платежа публикуется событие
PaymentConfirmed(
    payment_id=uuid4(),
    financial_subject_id=uuid4(),
    payer_owner_id=uuid4(),
    cooperative_id=uuid4(),
    amount=Decimal("100.00"),
    payment_date=date.today(),
)

# PaymentConfirmedHandler автоматически:
# 1. Создаёт/находит Member
# 2. Зачисляет на PersonalAccount
# 3. Распределяет по долгам (если есть)
```

### 2. Получение баланса

```http
GET /api/financial-subjects/{id}/balance?as_of_date=2026-03-20
Authorization: Bearer {token}

Response:
{
  "financial_subject_id": "...",
  "total_accruals": "1000.00",
  "total_payments": "600.00",
  "balance": "400.00"  # положительный = долг
}
```

### 3. Получение лицевого счёта

```http
GET /api/payment-distribution/members/{id}/account
Authorization: Bearer {token}

Response:
{
  "account_number": "PA-abc123-def456",
  "balance": "150.00",  # положительный = аванс
  "status": "active"
}
```

---

## Проверка качества

```bash
# Запуск тестов
cd backend
pytest

# Lint
ruff check .
ruff format --check .

# Seed (тестовые данные)
python -m app.scripts.seed_db
```

**Ожидаемый результат:** все тесты проходят, ruff чистый, seed выполняется при необходимости (проверять актуальным прогоном).

---

## Ссылки

- [Development Index](docs/development-index.md)
- [Финансовая модель — план](docs/plan/financial-model-optimization/INDEX.md)
- [ADR 0002](docs/architecture/adr/0002-financial-temporal-and-ledger-ready.md)
- [ADR 0003](docs/architecture/adr/0003-payment-distribution-model.md)
- [ADR 0004](docs/architecture/adr/0004-balance-cqrs-snapshots.md)
- [ER-диаграмма](docs/data-model/payment-distribution-erd.md)

---

*Первоначально: 2026-03-20 (фазы 1–3). Обновлено: 2026-03-22 (фазы 4–5, единый статус с [`INDEX.md`](INDEX.md)).*
