# Фаза 1: Фундамент

**Цель:** Заложить основу для всех последующих фаз — добавить `due_date`, довести правило баланса до полноты по ADR 0002, ввести Money Value Object.

**Зависимости:** нет.  
**Оценка:** 2–3 сессии.  
**Ветка:** `feature/fin-model-phase-1`

---

## Задача 1.1: Добавить `due_date` на начисление (Accrual)

### Проблема

У начисления есть `accrual_date` (когда начислили) и `period_start/period_end` (за какой период), но нет срока оплаты. Без `due_date`:
- невозможно автоматически считать пени (неизвестно, с какого дня просрочка);
- нельзя формировать уведомления «оплатите до...»;
- нельзя приоритизировать старые долги при распределении платежа.

### Что сделать

**Domain** (`backend/app/modules/accruals/domain/entities.py`):
- Добавить поле `due_date: date | None = None` в dataclass `Accrual`.
- Семантика: дата, до которой начисление должно быть оплачено. Если None — срок не установлен (например, разовое начисление без дедлайна).

**Infrastructure** (`backend/app/modules/accruals/infrastructure/models.py`):
- Добавить столбец `due_date = mapped_column(Date, nullable=True)` в `AccrualModel`.
- Добавить в `AccrualHistoryModel`.
- Обновить `to_domain()` и `from_domain()`.

**Application** (`backend/app/modules/accruals/application/dtos.py`):
- Добавить `due_date: date | None = None` в `AccrualCreate`, `AccrualInDB`.

**API** (`backend/app/modules/accruals/api/routes.py`):
- При создании: клиент может передать `due_date` (опционально).
- При массовом создании (`MassCreateAccrualsUseCase`): `due_date` задаётся для всех начислений партии.
- В ответах: `due_date` возвращается.

**Миграция Alembic:**
- Новый столбец `due_date` (Date, nullable) в таблице `accruals`.
- Добавить в `accruals_history`.

**Seed** (`backend/app/scripts/seed_db.py`):
- В тестовых начислениях задать `due_date` (например, +30 дней от `accrual_date`).

### Тесты

- Создание начисления с `due_date` — поле сохраняется и возвращается.
- Создание без `due_date` — поле = null, ошибки нет.
- Массовое создание — `due_date` применяется ко всем.

### Файлы для изменения

```
backend/app/modules/accruals/domain/entities.py
backend/app/modules/accruals/infrastructure/models.py
backend/app/modules/accruals/application/dtos.py
backend/app/modules/accruals/api/routes.py
backend/app/modules/accruals/application/use_cases.py
backend/alembic/versions/  (новая миграция)
backend/app/scripts/seed_db.py
backend/app/db/history_events.py  (добавить due_date в snapshot_columns)
backend/tests/test_api/test_accruals.py
backend/tests/test_models/test_accrual.py
```

---

## Задача 1.2: Исправить правило баланса на дату (ADR 0002)

### Проблема

По ADR 0002, операция участвует в балансе на дату X, если:
1. `event_date <= X`
2. `date(created_at) <= X`
3. `(status ≠ cancelled) OR (cancelled_at IS NOT NULL AND date(cancelled_at) > X)`

В текущем коде `BalanceRepository` (financial_core/infrastructure/repositories.py):
- Условие 1: реализовано (`accrual_date <= as_of_date`, `payment_date <= as_of_date`).
- Условие 2: **НЕ реализовано** — нет фильтра по `created_at`.
- Условие 3: реализовано, но для начислений используется `status == "applied"`, что исключает отменённые начисления, даже если `cancelled_at > X`.

### Что сделать

**Infrastructure** (`backend/app/modules/financial_core/infrastructure/repositories.py`):

В методах `calculate_balance` и `get_balances_by_cooperative`:

Для **начислений** (Accrual) заменить текущий фильтр на:
```python
and_(
    AccrualModel.accrual_date <= as_of_date,
    func.date(AccrualModel.created_at) <= as_of_date,
    or_(
        AccrualModel.status == "applied",
        and_(
            AccrualModel.status == "cancelled",
            AccrualModel.cancelled_at.isnot(None),
            func.date(AccrualModel.cancelled_at) > as_of_date
        )
    )
)
```

Для **платежей** (Payment) — аналогично:
```python
and_(
    PaymentModel.payment_date <= as_of_date,
    func.date(PaymentModel.created_at) <= as_of_date,
    or_(
        PaymentModel.status == "confirmed",
        and_(
            PaymentModel.status == "cancelled",
            PaymentModel.cancelled_at.isnot(None),
            func.date(PaymentModel.cancelled_at) > as_of_date
        )
    )
)
```

### Тесты

Сценарий: создать начисление (accrual_date=1 марта, created_at=1 марта, applied). Отменить его 5 марта (cancelled_at=5 марта).

- Баланс на 3 марта: начисление **входит** (отмена произошла позже).
- Баланс на 6 марта: начисление **не входит** (уже отменено).
- Баланс на 28 февраля: начисление **не входит** (event_date > X).

Сценарий (created_at): создать начисление 10 марта за период 1–31 января (accrual_date=31 января, created_at=10 марта).

- Баланс на 5 марта: начисление **не входит** (created_at > 5 марта).
- Баланс на 15 марта: начисление **входит**.

### Файлы для изменения

```
backend/app/modules/financial_core/infrastructure/repositories.py
backend/tests/test_api/test_financial_subjects.py  (новые тест-кейсы)
```

---

## Задача 1.3: Money Value Object

### Проблема

Все суммы (`amount`) — `Decimal` без обёртки. Нет защиты от:
- случайного сложения суммы и не-суммы;
- потери точности при округлении;
- разброса логики форматирования/округления по коду.

### Что сделать

**Shared kernel** — создать `backend/app/modules/shared/kernel/money.py`:

```python
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: Decimal

    CURRENCY = "BYN"
    PRECISION = Decimal("0.01")

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        return Money(self.amount - other.amount)

    def __neg__(self) -> "Money":
        return Money(-self.amount)

    def __gt__(self, other: "Money") -> bool:
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        return self.amount >= other.amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount

    def rounded(self) -> "Money":
        return Money(self.amount.quantize(self.PRECISION, rounding=ROUND_HALF_UP))

    @property
    def is_zero(self) -> bool:
        return self.amount == Decimal("0")

    @property
    def is_positive(self) -> bool:
        return self.amount > Decimal("0")

    @property
    def is_negative(self) -> bool:
        return self.amount < Decimal("0")

    @classmethod
    def zero(cls) -> "Money":
        return cls(Decimal("0"))
```

### Стратегия внедрения (постепенная)

**Фаза 1** — только создать Money и использовать в `BalanceCalculator`:

- `financial_core/domain/services.py`: `BalanceCalculator.calculate(total_accruals: Money, total_payments: Money) -> Money`.
- `financial_core/domain/entities.py`: в `Balance` поля `total_accruals`, `total_payments`, `balance` — тип `Money`.

**Позже (фаза 2–3)** — внедрять в Accrual, Payment, Expense entity по мере рефакторинга. Не менять всё сразу — это сломает слишком много.

На уровне ORM и API суммы остаются `Decimal`; конвертация Money ↔ Decimal — в маппинге `to_domain()` / `from_domain()` и в DTO.

### Тесты

- `Money(10) + Money(5) == Money(15)`.
- `Money(10) - Money(3) == Money(7)`.
- `Money(10.005).rounded() == Money(10.01)` (BYN — 2 знака).
- `Money.zero().is_zero == True`.
- BalanceCalculator с Money возвращает правильные значения.

### Файлы для изменения

```
backend/app/modules/shared/kernel/money.py  (НОВЫЙ)
backend/app/modules/financial_core/domain/services.py
backend/app/modules/financial_core/domain/entities.py
backend/app/modules/financial_core/infrastructure/repositories.py  (маппинг Decimal → Money)
backend/tests/test_core/test_money.py  (НОВЫЙ)
backend/tests/test_core/test_balance_calculator.py  (обновить)
```

---

## Критерий приёмки фазы 1

- [ ] `due_date` доступен в API создания и ответах начислений.
- [ ] Баланс на дату корректно учитывает `created_at` и `cancelled_at > X`.
- [ ] Тесты на баланс с backdated-операциями и отменами проходят.
- [ ] `Money` создан и используется в `BalanceCalculator` и `Balance`.
- [ ] Все существующие тесты проходят; ruff чист.
- [ ] Миграция применяется на чистую базу и поверх существующих данных.
- [ ] `seed_db` работает с `due_date`.

---

*Следующая фаза: [phase-2-balance-architecture.md](phase-2-balance-architecture.md)*
