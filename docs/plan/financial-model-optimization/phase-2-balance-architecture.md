# Фаза 2: Архитектура баланса

**Цель:** Устранить нарушение Clean Architecture в расчёте баланса, выделить правило участия операций в спецификацию, подготовить основу для CQRS (read-model баланса).

**Зависимости:** Фаза 1 (Money Value Object, исправленное правило баланса).  
**Оценка:** 2–3 сессии.  
**Ветка:** `feature/fin-model-phase-2`

---

## Контекст: что сейчас не так

`BalanceRepository` в `financial_core/infrastructure/repositories.py` **напрямую импортирует** `AccrualModel` из `accruals/infrastructure/models.py` и `PaymentModel` из `payments/infrastructure/models.py`. Это нарушение: модуль `financial_core` (infrastructure слой) зависит от **infrastructure** других модулей.

Правильно: financial_core должен получать данные для расчёта баланса через **интерфейсы**, а не через прямые join-ы с чужими ORM-моделями.

Кроме того, правило «какие операции участвуют в балансе» — это **доменное знание**, а не деталь реализации SQL-запроса. Оно должно быть отдельным доменным объектом (Specification).

---

## Задача 2.1: Specification Pattern — правило участия в балансе

### Что сделать

**Domain** — создать `backend/app/modules/financial_core/domain/balance_spec.py`:

```python
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class BalanceParticipationRule:
    """Правило: участвует ли операция в балансе на дату as_of_date."""
    as_of_date: date

    def accrual_participates(
        self,
        accrual_date: date,
        created_at_date: date,
        status: str,
        cancelled_at_date: date | None,
    ) -> bool:
        if accrual_date > self.as_of_date:
            return False
        if created_at_date > self.as_of_date:
            return False
        if status == "applied":
            return True
        if status == "cancelled" and cancelled_at_date and cancelled_at_date > self.as_of_date:
            return True
        return False

    def payment_participates(
        self,
        payment_date: date,
        created_at_date: date,
        status: str,
        cancelled_at_date: date | None,
    ) -> bool:
        if payment_date > self.as_of_date:
            return False
        if created_at_date > self.as_of_date:
            return False
        if status == "confirmed":
            return True
        if status == "cancelled" and cancelled_at_date and cancelled_at_date > self.as_of_date:
            return True
        return False
```

**Зачем:**
- Тестируется **без БД** — чистый Python.
- Используется в двух местах: 1) SQL-фильтр в BalanceRepository (трансляция в WHERE), 2) in-memory проверка в тестах/отчётах.
- При изменении правила — одно место для правки.

### Трансляция в SQL (Translator)

> **Решение (принято 2026-03-19):** Чтобы не дублировать логику правила в Python и в SQL-фильтрах, рядом с `BalanceParticipationRule` создаётся **translator** — класс `BalanceParticipationSqlFilter`, который читает ту же спецификацию и генерирует SQLAlchemy WHERE-выражения.

```python
# financial_core/infrastructure/balance_spec_sql.py
class BalanceParticipationSqlFilter:
    """Транслирует BalanceParticipationRule в SQLAlchemy WHERE-клаузы."""

    def __init__(self, rule: BalanceParticipationRule):
        self._rule = rule

    def accrual_filter(self, model: type[AccrualModel]):
        """Возвращает SQLAlchemy BooleanClauseList для фильтрации начислений."""
        ...

    def payment_filter(self, model: type[PaymentModel]):
        """Возвращает SQLAlchemy BooleanClauseList для фильтрации платежей."""
        ...
```

**Правило:** логика — в `BalanceParticipationRule` (domain). SQL — производная через translator (infrastructure). При изменении правила — меняется только спецификация и translator, а не SQL в репозиториях напрямую.

### Тесты

- Unit-тесты на `BalanceParticipationRule` с разными комбинациями дат и статусов (матрица: applied/confirmed/cancelled × дата до/после/равна X × cancelled_at до/после/null).
- Минимум 10 кейсов.
- **Интеграционный тест-согласованности:** проверяет, что результаты Python-спецификации и SQL-фильтра (через translator) совпадают на одних и тех же данных.

### Файлы

```
backend/app/modules/financial_core/domain/balance_spec.py  (НОВЫЙ)
backend/app/modules/financial_core/infrastructure/balance_spec_sql.py  (НОВЫЙ — translator)
backend/tests/test_core/test_balance_spec.py  (НОВЫЙ)
backend/tests/test_core/test_balance_spec_sql_consistency.py  (НОВЫЙ — тест согласованности)
```

---

## Задача 2.2: Устранить зависимость BalanceRepository от чужих моделей

### Проблема

`financial_core/infrastructure/repositories.py` импортирует:
- `AccrualModel` из `accruals/infrastructure/models.py`
- `PaymentModel` из `payments/infrastructure/models.py`

Это связывает модули на уровне инфраструктуры. Если accruals переименует столбец — financial_core сломается.

### Варианты решения

**Вариант A: Агрегатные данные через интерфейсы.**

В `IBalanceRepository` интерфейс остаётся тот же, но реализация получает агрегированные суммы через вспомогательные интерфейсы:

```python
# financial_core/domain/repositories.py
class IAccrualAggregateProvider(ABC):
    async def sum_participating(
        self, financial_subject_id: UUID, as_of_date: date
    ) -> Decimal: ...

class IPaymentAggregateProvider(ABC):
    async def sum_participating(
        self, financial_subject_id: UUID, as_of_date: date
    ) -> Decimal: ...
```

Реализации этих интерфейсов — в `accruals/infrastructure/` и `payments/infrastructure/` соответственно. BalanceRepository вызывает их через DI.

**Вариант B: SQL view / materialized view.**

Создать SQL view `v_accrual_amounts` и `v_payment_amounts` на уровне БД. BalanceRepository работает с views, не зная о моделях.

**Рекомендация:** Вариант A — чище, не зависит от специфики БД, легче тестировать.

### Что сделать (Вариант A)

1. **Domain** (`financial_core/domain/repositories.py`):
   - Добавить `IAccrualAggregateProvider` и `IPaymentAggregateProvider` (см. выше).

2. **Infrastructure — accruals** (`accruals/infrastructure/repositories.py`):
   - Добавить класс `AccrualAggregateProvider(IAccrualAggregateProvider)`.
   - Метод `sum_participating` — SQL-запрос с фильтрами из `BalanceParticipationRule` (транслированными в SQLAlchemy WHERE).
   - Метод `sum_participating_by_cooperative(cooperative_id, as_of_date)` — для группового расчёта.

3. **Infrastructure — payments** (`payments/infrastructure/repositories.py`):
   - Аналогично: `PaymentAggregateProvider(IPaymentAggregateProvider)`.

4. **Infrastructure — financial_core** (`financial_core/infrastructure/repositories.py`):
   - `BalanceRepository.__init__` принимает `IAccrualAggregateProvider` и `IPaymentAggregateProvider` через DI.
   - Метод `calculate_balance` вызывает `accrual_provider.sum_participating(fs_id, as_of_date)` и `payment_provider.sum_participating(fs_id, as_of_date)`.
   - Удалить прямые импорты `AccrualModel`, `PaymentModel`.

5. **DI** (`backend/app/modules/deps.py`):
   - Зарегистрировать `AccrualAggregateProvider` и `PaymentAggregateProvider`.
   - Передать их в `BalanceRepository`.

### Тесты

- BalanceRepository с mock-провайдерами: передаём заранее известные суммы, проверяем формулу.
- AccrualAggregateProvider: интеграционный тест с реальными данными и проверкой правила на дату.
- PaymentAggregateProvider: аналогично.

### Файлы

```
backend/app/modules/financial_core/domain/repositories.py  (добавить интерфейсы)
backend/app/modules/accruals/infrastructure/repositories.py  (добавить AccrualAggregateProvider)
backend/app/modules/payments/infrastructure/repositories.py  (добавить PaymentAggregateProvider)
backend/app/modules/financial_core/infrastructure/repositories.py  (рефакторинг BalanceRepository)
backend/app/modules/deps.py  (DI)
backend/tests/test_api/test_financial_subjects.py  (обновить)
```

---

## Задача 2.3: Подготовка к CQRS — денормализованный баланс (проект)

### Проблема

Каждый запрос баланса пересчитывает `SUM(accruals) - SUM(payments)` за всё время. При росте данных (500+ участков × годы операций) — это медленно.

### Что спроектировать (НЕ реализовывать целиком в этой фазе)

**Концепция: таблица `balance_snapshots`.**

```
balance_snapshots:
  id: UUID
  financial_subject_id: UUID (FK)
  snapshot_date: date
  total_accruals: Decimal
  total_payments: Decimal
  balance: Decimal
  created_at: datetime
```

**Обновление:** при каждом событии (AccrualApplied, AccrualCancelled, PaymentConfirmed, PaymentCancelled) — обработчик обновляет snapshot для текущей даты.

**Чтение:** `GET /balance` сначала ищет snapshot; если нет — считает из операций (fallback).

### Что сделать в этой фазе

1. **ADR** — написать черновик ADR 0004: «CQRS для баланса: читай из snapshot, пиши из событий».
2. **Не делать:** `BalanceSnapshot` dataclass, ORM-модель, миграцию, обработчики событий — всё это фаза 4 (после периодов). Не класть код, который никто не использует.

> **Решение (принято 2026-03-19):** BalanceSnapshot dataclass создаётся в фазе 4, когда он реально нужен. В фазе 2 — только ADR-черновик.

### Файлы

```
docs/architecture/adr/0004-balance-cqrs-snapshots.md  (НОВЫЙ — черновик)
```

---

## Критерий приёмки фазы 2

- [ ] `BalanceParticipationRule` — отдельный доменный объект с полным набором unit-тестов.
- [ ] `BalanceRepository` **не импортирует** AccrualModel / PaymentModel напрямую.
- [ ] `AccrualAggregateProvider` и `PaymentAggregateProvider` зарегистрированы в DI.
- [ ] Все существующие тесты баланса проходят с новой архитектурой.
- [ ] ADR 0004 (черновик) описывает путь к CQRS. BalanceSnapshot dataclass — **не создавать** (фаза 4).
- [ ] ruff чист; pytest проходит.

---

*Предыдущая фаза: [phase-1-foundation.md](phase-1-foundation.md)*  
*Следующая фаза: [phase-3-payment-distribution.md](phase-3-payment-distribution.md)*
