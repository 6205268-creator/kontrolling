# Фаза 4: Финансовые периоды и отчётность

**Цель:** Ввести концепцию финансового периода, возможность закрытия периода, снимки балансов (balance snapshots), основу для оборотных ведомостей.

**Зависимости:** Фаза 2 (баланс на дату), Фаза 3 (распределение для детализации).  
**Оценка:** 2–3 сессии.  
**Ветка:** `feature/fin-model-phase-4`

---

## Контекст

Сейчас в системе нет понятия «месяц закрыт» или «годовой период». Операции создаются/отменяются без ограничений по времени. Это значит:
- Казначей может задним числом менять данные за прошлый год.
- Нет оборотной ведомости (нужно: сальдо на начало, обороты за период, сальдо на конец).
- Нет сравнительных отчётов.

---

## Задача 4.1: Сущность FinancialPeriod

### Domain entity

> **Решение (принято 2026-03-19):** Вместо `month: int` с магическим значением `0` для годового периода — используем enum `PeriodType` и `month: int | None`.

```python
from enum import StrEnum

class PeriodType(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

@dataclass
class FinancialPeriod:
    id: UUID
    cooperative_id: UUID
    period_type: PeriodType   # monthly / yearly
    year: int
    month: int | None         # 1–12 для monthly; None для yearly
    start_date: date          # первый день периода
    end_date: date            # последний день периода
    status: str               # "open" / "closed" / "locked"
    closed_at: datetime | None = None
    closed_by_user_id: UUID | None = None
```

### Статусы

| Статус | Что можно | Что нельзя |
|--------|-----------|------------|
| `open` | Всё: создавать, отменять операции в этом периоде | — |
| `closed` | Просмотр, отчёты; казначей может переоткрыть в течение N дней | Новые операции, отмены в этом периоде |
| `locked` | Только просмотр | Переоткрытие без участия admin |

### Бизнес-правила

1. При создании Accrual / Payment: проверить, что период, в который попадает `accrual_date` / `payment_date`, имеет статус `open`. Если нет — отклонить (400 Bad Request).
2. При отмене: проверить, что период `event_date` операции — `open`.
3. Период можно закрыть, только если предыдущий период уже закрыт (нельзя закрыть март, если февраль ещё открыт).
4. Периоды создаются вручную или автоматически при первой операции за месяц.

### Правила переоткрытия периода (подтверждено с владельцем)

- **Казначей** может переоткрыть период (`closed → open`), если с момента закрытия прошло не более `period_reopen_allowed_days` дней.
- **Admin** может переоткрыть в любое время, включая `locked`.
- Настройка `period_reopen_allowed_days` хранится в таблице настроек СТ (`CooperativeSettings`), значение по умолчанию — 30 дней.
- После истечения `period_reopen_allowed_days` период автоматически переходит в статус `locked` (или при явной блокировке admin'ом).

### Решённый вопрос: платёж за закрытый период

> **Решение (принято 2026-03-19):** Запрещать (400 Bad Request). Если приходит платёж с датой в закрытом периоде — система возвращает ошибку. Казначей должен: 1) переоткрыть период, 2) внести платёж, 3) закрыть период снова. Строгий контроль, не ломает отчётность.

### Что сделать

**Domain** — `backend/app/modules/financial_core/domain/entities.py`:
- Добавить `FinancialPeriod` dataclass.
- Добавить метод `close(closed_by: UUID, now: datetime)` — проверка, что статус = open, установка closed.

**Domain repository** — `financial_core/domain/repositories.py`:
- `IFinancialPeriodRepository`: `get_by_date(cooperative_id, date)`, `get_all(cooperative_id, year)`, `add`, `update`.

**Infrastructure** — ORM модель:
- Таблица `financial_periods`: id, cooperative_id, year, month, start_date, end_date, status, closed_at, closed_by_user_id.
- Уникальность: (cooperative_id, year, month) для monthly; (cooperative_id, year) для yearly.

**Application** — use cases:
- `CreateFinancialPeriodUseCase` (или auto-create при первой операции).
- `CloseFinancialPeriodUseCase` — закрыть период.
- `ReopenFinancialPeriodUseCase` — переоткрыть. Логика:
  - Казначей: разрешено, если `now - closed_at <= period_reopen_allowed_days` (из CooperativeSettings).
  - Admin: разрешено всегда, в том числе из `locked`.
- `LockFinancialPeriodUseCase` — заблокировать (admin или автоматически по истечении дней).
- `GetFinancialPeriodsUseCase` — список периодов по СТ.

**CooperativeSettings** — добавить поле:
- `period_reopen_allowed_days: int` — количество дней, в течение которых казначей может переоткрыть закрытый период (по умолчанию 30).

**API** — `financial_core/api/routes.py`:
- `GET /periods?cooperative_id=&year=` — список периодов.
- `POST /periods` — создать период.
- `POST /periods/{id}/close` — закрыть.
- `POST /periods/{id}/reopen` — переоткрыть (казначей — в пределах N дней; admin — всегда).
- `POST /periods/{id}/lock` — заблокировать (admin only).

**Интеграция с accruals/payments:**

В `CreateAccrualUseCase` и `RegisterPaymentUseCase` — перед созданием:
```python
period = await period_repo.get_by_date(cooperative_id, event_date)
if period and period.status != "open":
    raise DomainError(f"Период {period.year}-{period.month} закрыт")
```

Аналогично в `CancelAccrualUseCase` и `CancelPaymentUseCase`.

### Файлы

```
backend/app/modules/financial_core/domain/entities.py
backend/app/modules/financial_core/domain/repositories.py
backend/app/modules/financial_core/infrastructure/models.py
backend/app/modules/financial_core/infrastructure/repositories.py
backend/app/modules/financial_core/application/use_cases.py
backend/app/modules/financial_core/application/dtos.py
backend/app/modules/financial_core/api/routes.py
backend/app/modules/cooperative_core/domain/entities.py  (CooperativeSettings.period_reopen_allowed_days)
backend/app/modules/cooperative_core/infrastructure/models.py
backend/app/modules/deps.py
backend/app/db/register_models.py  (при новых таблицах)
backend/app/modules/accruals/application/use_cases.py  (проверка периода)
backend/app/modules/payments/application/use_cases.py  (проверка периода)
backend/tests/test_api/test_financial_periods.py  (НОВЫЙ)
```

---

## Задача 4.2: Balance Snapshots (реализация ADR 0004)

### Контекст

В фазе 2 спроектирован BalanceSnapshot (ADR 0004 черновик). Теперь реализуем.

### Что сделать

**Infrastructure** — ORM модель:
- Таблица `balance_snapshots`: id, financial_subject_id, period_id, snapshot_date, total_accruals, total_payments, balance, created_at.

**Создание snapshot:**

При **закрытии периода** (`CloseFinancialPeriodUseCase`):
1. Для каждого FinancialSubject данного cooperative_id:
   - Рассчитать баланс на `end_date` периода (через BalanceRepository).
   - Создать запись BalanceSnapshot.
2. Это гарантирует, что баланс на конец закрытого периода зафиксирован и не пересчитывается.

**Поведение при переоткрытии периода:**

> **Решение (принято 2026-03-19):** При переоткрытии периода (`ReopenFinancialPeriodUseCase`) все balance snapshots за этот период **удаляются**. При повторном закрытии — создаются заново с актуальными данными. Просто и надёжно: snapshots всегда соответствуют последнему закрытию.

**Чтение:**

`GetBalanceUseCase.execute(fs_id, as_of_date)`:
1. Если `as_of_date` попадает в закрытый период — вернуть snapshot (быстро, без SQL SUM).
2. Если в открытый период — рассчитать из операций (как сейчас).

### Тесты

- Закрыть период → проверить, что snapshots созданы для всех субъектов.
- Запросить баланс на дату закрытого периода → ответ из snapshot (проверить через mock/spy, что SUM не вызывается).
- Запросить баланс на дату открытого периода → расчёт из операций.

### Файлы

```
backend/app/modules/financial_core/infrastructure/models.py  (BalanceSnapshotModel)
backend/app/modules/financial_core/infrastructure/repositories.py  (snapshot CRUD)
backend/app/modules/financial_core/application/use_cases.py  (создание snapshot при закрытии)
backend/tests/test_api/test_balance_snapshots.py  (НОВЫЙ)
```

---

## Задача 4.3: Оборотная ведомость (Turnover Sheet)

### Что это

Классический финансовый отчёт:

| Субъект | Сальдо на начало | Начислено | Оплачено | Сальдо на конец |
|---------|------------------|-----------|----------|-----------------|

### Алгоритм

Для периода (year, month):
1. `сальдо_начало` = snapshot за предыдущий период (или расчёт, если нет snapshot).
2. `начислено` = сумма Accrual за период (event_date в [start_date, end_date], status = applied).
3. `оплачено` = сумма Payment за период (аналогично).
4. `сальдо_конец` = сальдо_начало + начислено - оплачено.

### Что сделать

**Reporting module** (`backend/app/modules/reporting/`):
- Use case: `GetTurnoverSheetUseCase(cooperative_id, year, month)`.
- Использует: `IBalanceRepository` (snapshot), `IAccrualAggregateProvider`, `IPaymentAggregateProvider`.
- Возвращает: список строк (по FinancialSubject) с четырьмя колонками.

**API** (`reporting/api/routes.py`):
- `GET /reports/turnover?cooperative_id=&year=&month=` → JSON с данными ведомости.

### Файлы

```
backend/app/modules/reporting/application/use_cases.py  (добавить GetTurnoverSheetUseCase)
backend/app/modules/reporting/application/dtos.py  (TurnoverSheetRow, TurnoverSheet)
backend/app/modules/reporting/api/routes.py  (эндпоинт)
backend/app/modules/deps.py  (DI)
backend/tests/test_api/test_reporting.py  (тест на ведомость)
```

---

## Критерий приёмки фазы 4

**Статус:** выполнено (2026-03-22). Интеграционные тесты: `backend/tests/test_api/test_financial_periods_phase4.py`. Частичный unique для годовых периодов задан в ORM — см. [`docs/plan/current-focus.md`](../current-focus.md), блок «Не дублировать: Фаза 4».

- [x] FinancialPeriod создаётся, закрывается, переоткрывается, блокируется.
- [x] Казначей может переоткрыть в пределах `period_reopen_allowed_days` дней.
- [x] Admin может переоткрыть всегда (включая `locked`).
- [x] После истечения дней — период переходит в `locked`, переоткрытие только admin.
- [x] `period_reopen_allowed_days` читается из настроек кооператива (`cooperatives.period_reopen_allowed_days`).
- [x] Создание/отмена операций в закрытом/locked периоде — отклонение с сообщением (`PeriodOperationGuard`).
- [x] При закрытии периода — balance snapshots для всех субъектов.
- [x] Запрос баланса на дату закрытого периода — из snapshot при наличии.
- [x] Оборотная ведомость возвращает корректные данные (`GET /api/reports/turnover`).
- [x] Тесты: периоды, снимки, turnover, reopen/lock, блокировка начислений — см. файл тестов выше.
- [x] pytest + ruff по затронутым модулям (регрессия зелёная на момент закрытия фазы).

---

*Предыдущая фаза: [phase-3-payment-distribution.md](phase-3-payment-distribution.md)*  
*Следующая фаза: [phase-5-debt-penalties.md](phase-5-debt-penalties.md)*
