# Промпт для верификации: Оптимизация финансовой модели

**Назначение:** Дать этот документ другой модели (AI-агенту). Модель проведёт аудит текущего состояния кода и заполнит таблицу статусов по каждому пункту.

---

## Инструкция для модели-аудитора

Ты — архитектурный аудитор проекта КОНТРОЛЛИНГ (система учёта для садоводческих товариществ). Тебе нужно проверить, насколько финансовая модель проекта соответствует плану оптимизации.

### Что делать

1. Прочитай план оптимизации: `docs/plan/financial-model-optimization/INDEX.md` (и при необходимости отдельные фазы).
2. Для **каждой строки** в таблице ниже:
   - Найди соответствующий код / файлы / тесты.
   - Определи статус: **Done** / **Partial** / **Not done**.
   - Заполни колонку «Что найдено» — краткое описание, что реально есть в коде (с путями к файлам и номерами строк).
   - Заполни колонку «Замечания» — что не так, чего не хватает, что нарушено.
3. В конце — дай общую оценку и список приоритетных действий.

### Где искать

- **Backend код:** `backend/app/modules/` (модули: financial_core, accruals, payments, expenses, payment_distribution, reporting)
- **Домен:** `*/domain/entities.py`, `*/domain/repositories.py`, `*/domain/services.py`, `*/domain/events.py`
- **Инфраструктура:** `*/infrastructure/models.py`, `*/infrastructure/repositories.py`
- **API:** `*/api/routes.py`
- **Application:** `*/application/use_cases.py`, `*/application/dtos.py`
- **Shared kernel:** `backend/app/modules/shared/`
- **Тесты:** `backend/tests/`
- **DI:** `backend/app/modules/deps.py`
- **ADR:** `docs/architecture/adr/`
- **Схема БД:** ORM + `create_all` при старте (`app/main.py`), без Alembic

### Формат ответа

Заполни таблицу ниже и верни её целиком. После таблицы — раздел «Итог».

---

## Таблица верификации

### Фаза 1: Фундамент

| # | Пункт проверки | Где искать | Статус | Что найдено | Замечания |
|---|----------------|-----------|--------|-------------|-----------|
| 1.1 | **due_date в Accrual (domain entity)** — поле `due_date: date \| None` в dataclass Accrual | `accruals/domain/entities.py` | | | |
| 1.2 | **due_date в ORM** — столбец `due_date` (Date, nullable) в AccrualModel | `accruals/infrastructure/models.py` | | | |
| 1.3 | **due_date в AccrualHistoryModel** — столбец в таблице истории | `accruals/infrastructure/models.py` | | | |
| 1.4 | **due_date в DTO** — поле в AccrualCreate и AccrualInDB | `accruals/application/dtos.py` | | | |
| 1.5 | **due_date в API** — принимается при создании, возвращается в ответах | `accruals/api/routes.py` | | | |
| 1.6 | **due_date в актуальной схеме** — столбец есть в ORM/таблице (создание из моделей) | `accruals/infrastructure/models.py`, старт приложения | | | |
| 1.7 | **due_date в seed_db** — тестовые данные содержат due_date | `backend/app/scripts/seed_db.py` | | | |
| 1.8 | **due_date в history_events** — в snapshot_columns | `backend/app/db/history_events.py` | | | |
| 1.9 | **Правило баланса: фильтр created_at** — `func.date(created_at) <= as_of_date` в SQL-запросе расчёта баланса | `financial_core/infrastructure/repositories.py`, метод `calculate_balance` | | | |
| 1.10 | **Правило баланса: cancelled_at для начислений** — условие `(status == 'applied') OR (status == 'cancelled' AND cancelled_at > as_of_date)` | `financial_core/infrastructure/repositories.py` | | | |
| 1.11 | **Правило баланса: cancelled_at для платежей** — аналогичное условие с `confirmed` | `financial_core/infrastructure/repositories.py` | | | |
| 1.12 | **Тесты: баланс с backdated-операцией** — начисление с created_at > as_of_date не входит в баланс | `backend/tests/` | | | |
| 1.13 | **Тесты: баланс с отменой после даты** — отменённая операция входит, если cancelled_at > as_of_date | `backend/tests/` | | | |
| 1.14 | **Money Value Object** — класс Money в shared kernel (frozen dataclass, арифметика, округление BYN) | `backend/app/modules/shared/kernel/money.py` | | | |
| 1.15 | **Money в BalanceCalculator** — сервис использует Money вместо голого Decimal | `financial_core/domain/services.py` | | | |
| 1.16 | **Money в Balance entity** — поля total_accruals, total_payments, balance — тип Money | `financial_core/domain/entities.py` | | | |
| 1.17 | **Тесты на Money** — unit-тесты на арифметику, округление, zero, is_positive | `backend/tests/` | | | |

### Фаза 2: Архитектура баланса

| # | Пункт проверки | Где искать | Статус | Что найдено | Замечания |
|---|----------------|-----------|--------|-------------|-----------|
| 2.1 | **BalanceParticipationRule** — отдельный доменный объект с методами `accrual_participates` и `payment_participates` | `financial_core/domain/balance_spec.py` | | | |
| 2.2 | **Тесты BalanceParticipationRule** — минимум 10 кейсов (матрица статусов × дат) | `backend/tests/` | | | |
| 2.3 | **IAccrualAggregateProvider** — интерфейс в financial_core domain | `financial_core/domain/repositories.py` | | | |
| 2.4 | **IPaymentAggregateProvider** — интерфейс в financial_core domain | `financial_core/domain/repositories.py` | | | |
| 2.5 | **AccrualAggregateProvider** — реализация в accruals infrastructure | `accruals/infrastructure/repositories.py` | | | |
| 2.6 | **PaymentAggregateProvider** — реализация в payments infrastructure | `payments/infrastructure/repositories.py` | | | |
| 2.7 | **BalanceRepository НЕ импортирует AccrualModel/PaymentModel** — проверить imports | `financial_core/infrastructure/repositories.py` | | | |
| 2.8 | **DI: провайдеры зарегистрированы** — в deps.py | `backend/app/modules/deps.py` | | | |
| 2.9 | **ADR 0004 (CQRS для баланса)** — черновик существует | `docs/architecture/adr/` | | | |
| 2.10 | **BalanceSnapshot entity** — dataclass в domain | `financial_core/domain/entities.py` | | | |

### Фаза 3: Распределение платежей

| # | Пункт проверки | Где искать | Статус | Что найдено | Замечания |
|---|----------------|-----------|--------|-------------|-----------|
| 3.1 | **MemberPlot удалён** (или не дублирует PlotOwnership) | `payment_distribution/infrastructure/models.py` | | | |
| 3.2 | **Member entity** — тонкая сущность (owner_id + cooperative_id + status) | `payment_distribution/domain/entities.py` | | | |
| 3.3 | **PersonalAccount entity** — с balance (Money), account_number, status | `payment_distribution/domain/entities.py` | | | |
| 3.4 | **PersonalAccountTransaction entity** — credit/debit, привязка к payment/distribution | `payment_distribution/domain/entities.py` | | | |
| 3.5 | **PaymentDistribution entity** — payment_id, financial_subject_id, accrual_id, amount, priority | `payment_distribution/domain/entities.py` | | | |
| 3.6 | **DistributePaymentUseCase** — алгоритм: загрузить долги → отсортировать по приоритету → распределить | `payment_distribution/application/use_cases.py` | | | |
| 3.7 | **Интеграция с PaymentConfirmed event** — обработчик вызывает зачисление + распределение | `payment_distribution/infrastructure/event_handlers.py` | | | |
| 3.8 | **Отмена платежа → reverse distributions** — при отмене все distributions reversed | `payment_distribution/application/use_cases.py` | | | |
| 3.9 | **API: состояние лицевого счёта** — GET эндпоинт | `payment_distribution/api/routes.py` | | | |
| 3.10 | **API: как распределён платёж** — GET эндпоинт | `payment_distribution/api/routes.py` | | | |
| 3.11 | **Тесты: частичная оплата** — платёж < долг | `backend/tests/` | | | |
| 3.12 | **Тесты: переплата** — платёж > долг, остаток на лицевом счёте | `backend/tests/` | | | |

### Фаза 4: Финансовые периоды и отчётность

| # | Пункт проверки | Где искать | Статус | Что найдено | Замечания |
|---|----------------|-----------|--------|-------------|-----------|
| 4.1 | **FinancialPeriod entity** — id, cooperative_id, year, month, status (open/closed/locked) | `financial_core/domain/entities.py` | | | |
| 4.2 | **FinancialPeriod ORM** — таблица financial_periods | `financial_core/infrastructure/models.py` | | | |
| 4.3 | **CloseFinancialPeriodUseCase** — закрытие с проверкой предыдущего периода | `financial_core/application/use_cases.py` | | | |
| 4.4 | **Проверка периода при создании операций** — CreateAccrual/RegisterPayment проверяют, что период open | `accruals/application/use_cases.py`, `payments/application/use_cases.py` | | | |
| 4.5 | **Проверка периода при отмене операций** — Cancel проверяет, что период open | `accruals/application/use_cases.py`, `payments/application/use_cases.py` | | | |
| 4.6 | **BalanceSnapshot ORM** — таблица balance_snapshots | `financial_core/infrastructure/models.py` | | | |
| 4.7 | **Snapshot создаётся при закрытии периода** — для всех FinancialSubject | `financial_core/application/use_cases.py` | | | |
| 4.8 | **GetBalance использует snapshot** — если дата в закрытом периоде | `financial_core/application/use_cases.py` или `infrastructure/repositories.py` | | | |
| 4.9 | **Оборотная ведомость (Turnover Sheet)** — use case + API endpoint | `reporting/application/use_cases.py`, `reporting/api/routes.py` | | | |
| 4.10 | **API: CRUD для периодов** — create, close, reopen, list | `financial_core/api/routes.py` | | | |

### Фаза 5: Долги и пени

| # | Пункт проверки | Где искать | Статус | Что найдено | Замечания |
|---|----------------|-----------|--------|-------------|-----------|
| 5.1 | **DebtLine entity** — original_amount, paid_amount, outstanding_amount, due_date, overdue_since | `financial_core/domain/entities.py` | | | |
| 5.2 | **DebtLine создаётся при AccrualApplied** — обработчик события | `financial_core/infrastructure/event_handlers.py` | | | |
| 5.3 | **DebtLine обновляется при PaymentDistributed** — paid_amount += distribution.amount | `financial_core/infrastructure/event_handlers.py` | | | |
| 5.4 | **PenaltySettings entity + ORM** — ставка, grace_period, contribution_type | `financial_core/domain/entities.py`, `financial_core/infrastructure/models.py` | | | |
| 5.5 | **PenaltyCalculator** — доменный сервис, формула: outstanding × rate × days | `financial_core/domain/services.py` | | | |
| 5.6 | **Тесты PenaltyCalculator** — min 5 кейсов (без просрочки, с grace period, разные ставки) | `backend/tests/` | | | |
| 5.7 | **CalculatePenaltiesUseCase** — расчёт без записи в БД | `financial_core/application/use_cases.py` | | | |
| 5.8 | **AccruePenaltiesUseCase** — идемпотентная фиксация пеней как Accrual | `financial_core/application/use_cases.py` | | | |
| 5.9 | **API: расчёт пеней** — GET endpoint (предварительный) | `financial_core/api/routes.py` или `reporting/` | | | |
| 5.10 | **API: фиксация пеней** — POST endpoint | `financial_core/api/routes.py` | | | |
| 5.11 | **Отчёт по должникам** — use case + API | `reporting/application/use_cases.py`, `reporting/api/routes.py` | | | |

### Общие архитектурные проверки

| # | Пункт проверки | Где искать | Статус | Что найдено | Замечания |
|---|----------------|-----------|--------|-------------|-----------|
| A.1 | **Domain НЕ импортирует Infrastructure** — ни один `*/domain/*.py` не содержит `from app.modules.*.infrastructure` | `backend/app/modules/*/domain/` | | | |
| A.2 | **Domain НЕ импортирует FastAPI/SQLAlchemy** | `backend/app/modules/*/domain/` | | | |
| A.3 | **API НЕ импортирует Infrastructure** — ни один `*/api/*.py` не содержит `from app.modules.*.infrastructure` | `backend/app/modules/*/api/` | | | |
| A.4 | **FinancialSubject — единственная точка входа в финансы** — Accrual и Payment НЕ ссылаются напрямую на LandPlot, Meter, Owner (только через financial_subject_id) | domain entities | | | |
| A.5 | **Soft delete** — финансовые операции используют status=cancelled, нет hard delete | domain entities, repositories | | | |
| A.6 | **amount immutability** — update в репозиториях НЕ обновляет amount | `*/infrastructure/repositories.py`, метод `update` | | | |
| A.7 | **operation_number** — уникальный, генерируется при создании, не меняется при update | domain entities, repositories, API | | | |
| A.8 | **Domain Events** — AccrualApplied, AccrualCancelled, PaymentConfirmed, PaymentCancelled объявлены и диспатчатся | domain events, use cases | | | |
| A.9 | **ADR 0002 (ledger-ready)** — статус: Принято (не черновик) | `docs/architecture/adr/0002-*.md` | | | |

---

## Формат итога

После заполнения таблицы предоставь:

### 1. Статистика

```
Фаза 1: X/17 Done, Y Partial, Z Not done
Фаза 2: X/10 Done, Y Partial, Z Not done
Фаза 3: X/12 Done, Y Partial, Z Not done
Фаза 4: X/10 Done, Y Partial, Z Not done
Фаза 5: X/11 Done, Y Partial, Z Not done
Архитектура: X/9 Done, Y Partial, Z Not done
ИТОГО: X/69 Done, Y Partial, Z Not done
```

### 2. Критические замечания (блокируют следующую фазу)

Список пунктов со статусом «Not done» или «Partial», которые блокируют работу.

### 3. Рекомендации

Что сделать в первую очередь (топ-5 по приоритету).

---

*Создан: 2026-03-19. Источник: критический анализ финансовой модели и план оптимизации (`docs/plan/financial-model-optimization/INDEX.md`).*
