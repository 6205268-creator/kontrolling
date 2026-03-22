# Фаза 5: Долги и пени

**Цель:** Ввести «долг» как отслеживаемую сущность (а не только расчётный баланс), реализовать расчёт пеней, подготовить основу для требований об оплате.

**Зависимости:** Фаза 1 (due_date), Фаза 3 (распределение), Фаза 4 (периоды).  
**Оценка:** 3–4 сессии.  
**Ветка:** `feature/fin-model-phase-5`

---

## Контекст

Сейчас «долг» — это просто `balance > 0` по FinancialSubject. Нет способа:
- Узнать, когда долг возник (нет `due_date` → нет «дней просрочки»).
- Зафиксировать сумму долга для требования (долг расчётный, меняется при каждой операции).
- Считать пени (нет ставок, нет привязки к конкретным неоплаченным начислениям).
- Отслеживать частичное погашение конкретного начисления.

Исходные требования (`docs/source-material/БИЗНЕС_ЛОГИКА_И_СТРУКТУРА_БД.md`, блок 5) описывают: PenaltySettings (процент, дата начала), Penalties (сумма задолженности, дни просрочки, сумма пеней).

---

## Задача 5.1: DebtLine — долг как сущность

### Концепция

**DebtLine** = конкретное неоплаченное (или частично оплаченное) обязательство:

```python
@dataclass
class DebtLine:
    id: UUID
    financial_subject_id: UUID
    accrual_id: UUID
    original_amount: Money        # исходная сумма начисления
    paid_amount: Money            # сколько оплачено (через PaymentDistribution)
    outstanding_amount: Money     # original_amount - paid_amount
    due_date: date                # из Accrual.due_date
    overdue_since: date | None    # due_date + 1, если outstanding > 0 после due_date
    status: str                   # "active" / "paid" / "written_off"
    created_at: datetime
```

### Бизнес-правила

1. DebtLine создаётся автоматически при применении начисления (`AccrualApplied` event).
2. `outstanding_amount` обновляется при каждом `PaymentDistribution`, направленном на этот accrual_id.
3. Когда `outstanding_amount = 0` → status = "paid".
4. `overdue_since` = `due_date + 1 день`, если на дату `due_date` outstanding > 0.
5. DebtLine **не удаляется** при отмене начисления — вместо этого status = "written_off".

### Существующие данные

> **Решение (принято 2026-03-19):** Перенос старых начислений в DebtLines **не делаем**. База поднимается с нуля; DebtLines создаются только для новых начислений через event handler `AccrualApplied`.

### Где разместить

**Модуль:** `financial_core` (это финансовое ядро, debt — часть финансовой модели).

**Domain** (`financial_core/domain/entities.py`): добавить DebtLine.

**Repository** (`financial_core/domain/repositories.py`):
- `IDebtLineRepository`: `get_by_financial_subject(fs_id)`, `get_overdue(cooperative_id, as_of_date)`, `add`, `update`.

**Infrastructure:** ORM модель, таблица `debt_lines`.

**Обработчик события** (`financial_core/infrastructure/event_handlers.py`):
- На `AccrualApplied` → создать DebtLine.
- На `AccrualCancelled` → пометить DebtLine как written_off.
- На `PaymentDistributed` (из фазы 3) → обновить paid_amount и outstanding_amount.

### Файлы

```
backend/app/modules/financial_core/domain/entities.py
backend/app/modules/financial_core/domain/repositories.py
backend/app/modules/financial_core/infrastructure/models.py
backend/app/modules/financial_core/infrastructure/repositories.py
backend/app/modules/financial_core/infrastructure/event_handlers.py
backend/app/modules/deps.py
```

---

## Задача 5.2: PenaltySettings — настройки расчёта пеней

### Domain entity

```python
@dataclass
class PenaltySettings:
    id: UUID
    cooperative_id: UUID
    contribution_type_id: UUID | None  # None = для всех типов
    is_enabled: bool
    daily_rate: Decimal               # процент пени в день (например, 0.03% = 0.0003)
    grace_period_days: int            # дней после due_date до начала начисления пеней
    effective_from: date
    effective_to: date | None = None
```

### Бизнес-правила

- Ставка пеней задаётся на уровне СТ, опционально — по виду взноса.
- Grace period: 10 дней (по умолчанию) — пени начинаются через 10 дней после due_date.
- Ставка: фиксированный процент в день от суммы задолженности.

### ContributionType для пеней

> **Решение (принято 2026-03-19):** В `seed_db.py` создаётся фиксированная seed-запись `ContributionType(code="PENALTY", name="Пени", is_system=True)`. Системный тип нельзя удалить или переименовать. Поле `is_system: bool` добавляется в `ContributionType` entity и ORM-модель.

Файлы (доп.):
```
backend/app/modules/accruals/domain/entities.py  (добавить is_system в ContributionType)
backend/app/modules/accruals/infrastructure/models.py  (добавить is_system в ContributionTypeModel)
backend/app/scripts/seed_db.py  (seed-запись PENALTY)
```

### Что сделать

**Domain** — `financial_core/domain/entities.py` или отдельный модуль `penalties/domain/entities.py` (при необходимости).

**Infrastructure** — ORM модель, таблица `penalty_settings`.

**API** — CRUD для PenaltySettings (admin / treasurer).

### Файлы

```
backend/app/modules/financial_core/domain/entities.py  (или penalties/domain/entities.py)
backend/app/modules/financial_core/infrastructure/models.py
backend/app/modules/financial_core/api/routes.py  (или penalties/api/routes.py)
```

---

## Задача 5.3: PenaltyCalculator — расчёт пеней

### Архитектурное решение (подтверждено с владельцем)

**PenaltyCalculator изолирован как стратегия.** Логика расчёта вынесена в отдельный модуль, чтобы формулу можно было поменять (например, перейти со простых процентов на сложные) без изменения остальной системы.

**Текущая формула (вариант А — простые проценты):**
- Пени = `outstanding_amount × daily_rate × overdue_days`
- База расчёта — **текущий остаток долга** (`outstanding_amount`, то есть после частичных оплат).
- При полной оплате долга пени **не списываются автоматически** — казначей решает вручную (write-off).

### Интерфейс стратегии

```python
# financial_core/domain/penalty_strategy.py
from abc import ABC, abstractmethod

class IPenaltyStrategy(ABC):
    @abstractmethod
    def calculate(
        self,
        outstanding_amount: Money,
        overdue_days: int,
        settings: PenaltySettings,
    ) -> Money: ...
```

### Реализация (вариант А)

```python
# financial_core/domain/penalty_strategy.py
class SimpleDailyPenaltyStrategy(IPenaltyStrategy):
    def calculate(
        self,
        outstanding_amount: Money,
        overdue_days: int,
        settings: PenaltySettings,
    ) -> Money:
        penalty = outstanding_amount.amount * settings.daily_rate * overdue_days
        return Money(penalty).rounded()
```

### Domain service — PenaltyCalculator

```python
class PenaltyCalculator:
    def __init__(self, strategy: IPenaltyStrategy):
        self._strategy = strategy

    def calculate(
        self,
        debt_line: DebtLine,
        settings: PenaltySettings,
        as_of_date: date,
    ) -> Money:
        if not settings.is_enabled:
            return Money.zero()
        if debt_line.due_date is None:
            return Money.zero()
        if debt_line.outstanding_amount.is_zero:
            return Money.zero()

        penalty_start = debt_line.due_date + timedelta(days=settings.grace_period_days + 1)
        if as_of_date < penalty_start:
            return Money.zero()

        overdue_days = (as_of_date - penalty_start).days + 1
        return self._strategy.calculate(debt_line.outstanding_amount, overdue_days, settings)
```

### Бизнес-правила (подтверждено)

1. Пени считаются только для DebtLine с status="active" и `outstanding_amount > 0`.
2. Пени начинаются через `grace_period_days` после `due_date`.
3. База расчёта — текущий остаток долга (`outstanding_amount`), не исходная сумма.
4. Расчёт — **не создаёт записей** в БД. Read-only на указанную дату.
5. Фиксация пеней — отдельный шаг (создать Accrual типа «пени»).
6. При полной оплате долга пени **не списываются автоматически** — только вручную казначеем (операция write-off).

### Автоматическое начисление пеней

**Пени начисляются автоматически** по расписанию. Ручная корректировка (просмотр, write-off) всегда доступна казначею.

Scheduler (`APScheduler` или аналог):
- Запускает `AccruePenaltiesUseCase` с заданной периодичностью (например, 1-го числа каждого месяца).
- Настройка расписания — в `CooperativeSettings` (поле `penalty_accrual_schedule`, например `"monthly"` / `"weekly"`).

### Use case

`CalculatePenaltiesUseCase(cooperative_id, as_of_date)`:
1. Загрузить все active DebtLines с `overdue_since <= as_of_date`.
2. Для каждого: найти PenaltySettings (по contribution_type или общие).
3. Вызвать `PenaltyCalculator.calculate`.
4. Вернуть список: (debt_line_id, financial_subject_id, outstanding, overdue_days, penalty_amount).

`AccruePenaltiesUseCase(cooperative_id, as_of_date)`:
1. Вызвать `CalculatePenaltiesUseCase`.
2. Для каждой строки с penalty > 0: создать Accrual с `contribution_type="penalty"`, `amount=penalty`, `accrual_date=as_of_date`.
3. Идемпотентно: если пени за этот период уже начислены — не дублировать (проверка по period + contribution_type + financial_subject).

`WriteOffPenaltyUseCase(accrual_id, reason, user_id)`:
1. Проверить, что Accrual имеет `contribution_type="penalty"` и не отменён.
2. Отменить начисление (status = cancelled, cancelled_by = user_id, reason).
3. Это действие казначея — для каждого случая вручную.

### API

- `GET /penalties/calculate?cooperative_id=&as_of_date=` — предварительный расчёт (без записи).
- `POST /penalties/accrue?cooperative_id=&as_of_date=` — зафиксировать (создать начисления); также вызывается scheduler'ом.
- `POST /penalties/{accrual_id}/write-off` — списать пени вручную (казначей).
- `GET /penalties/settings?cooperative_id=` — настройки.
- `POST /penalties/settings` — создать/обновить настройки.

### Файлы

```
backend/app/modules/financial_core/domain/penalty_strategy.py  (НОВЫЙ — IPenaltyStrategy, SimpleDailyPenaltyStrategy)
backend/app/modules/financial_core/domain/services.py  (PenaltyCalculator принимает IPenaltyStrategy)
backend/app/modules/financial_core/application/use_cases.py  (CalculatePenalties, AccruePenalties, WriteOffPenalty)
backend/app/modules/financial_core/application/dtos.py  (PenaltyCalcResult)
backend/app/modules/financial_core/api/routes.py  (эндпоинты)
backend/app/modules/cooperative_core/domain/entities.py  (CooperativeSettings.penalty_accrual_schedule)
backend/app/scheduler.py  (или аналог — задача для AccruePenalties)
backend/app/modules/deps.py  (DI: зарегистрировать SimpleDailyPenaltyStrategy)
backend/tests/test_core/test_penalty_strategy.py  (НОВЫЙ)
backend/tests/test_core/test_penalty_calculator.py  (НОВЫЙ)
backend/tests/test_api/test_penalties.py  (НОВЫЙ)
backend/tests/test_api/test_phase5_penalties_integration.py  (НОВЫЙ — полный цикл: начисление → долг → платёж → пени)
```

---

## Задача 5.4: Отчёт по задолженностям (Debtors Report)

### Что это

Список должников по СТ на дату:

| Субъект | Владелец | Участок | Долг | Просрочка (дни) | Пени | Итого |
|---------|----------|---------|------|-----------------|------|-------|

### Use case

`GetDebtorsReportUseCase(cooperative_id, as_of_date)`:
1. Загрузить DebtLines с outstanding > 0.
2. Для каждого: рассчитать пени через PenaltyCalculator.
3. JOIN с FinancialSubject → LandPlot/Meter → Owner (через PlotOwnership / Meter.owner_id).
4. Вернуть строки с деталями.

### API

`GET /reports/debtors?cooperative_id=&as_of_date=`

### Файлы

```
backend/app/modules/reporting/application/use_cases.py  (GetDebtorsReportUseCase)
backend/app/modules/reporting/application/dtos.py  (DebtorRow)
backend/app/modules/reporting/api/routes.py
backend/tests/test_api/test_reporting.py
```

---

## Критерий приёмки фазы 5

- [x] DebtLine создаётся автоматически при применении начисления. *(API: `tests/test_api/test_phase5_penalties_integration.py`)*
- [x] При погашении через PaymentDistribution — `outstanding_amount` обновляется. *(тот же файл + общий `conftest`: одна БД для HTTP и обработчиков событий)*
- [x] PenaltySettings: CRUD работает. *( `tests/test_api/test_penalties.py` )*
- [x] `IPenaltyStrategy` изолирован; `SimpleDailyPenaltyStrategy` подключается через DI. *( `tests/test_core/test_penalty_strategy.py` )*
- [x] `PenaltyCalculator` считает от `outstanding_amount` (текущего остатка, а не исходной суммы). *(юнит + интеграция с частичной оплатой)*
- [x] `AccruePenalties`: идемпотентный, создаёт начисления типа «пени». *(интеграция `test_phase5_accrue_penalties_idempotent`)*
- [x] Автоматический scheduler запускает `AccruePenalties` по расписанию. *(`app/scheduler.py`, APScheduler; условия `penalty_accrual_schedule` по кооперативу)*
- [x] `WriteOffPenalty`: казначей может вручную списать пени для конкретного начисления. *(интеграция + `test_write_off_non_penalty_rejected`)*
- [x] При полной оплате долга пени **не списываются автоматически** *(расчёт по строке долга пустой после полного погашения основного начисления; отдельные начисления-пени не трогаются)*.
- [x] Отчёт по должникам: корректные данные с пенями. *(`GET /api/reports/debtors`, `backend/tests/test_api/test_reports.py` — сценарии `test_get_debtors_report*` и связанные)*
- [x] Тесты: минимум 10 кейсов (без просрочки, с просрочкой, частичная оплата, grace period, отключённые пени, разные ставки, write-off, повторный запуск accrue — идемпотентность). *( `test_penalty_strategy.py` + интеграция фазы 5 + `test_penalties.py` )*
- [x] pytest + ruff чисто.

---

*Предыдущая фаза: [phase-4-periods-reporting.md](phase-4-periods-reporting.md)*  
*Индекс: [INDEX.md](INDEX.md)*
