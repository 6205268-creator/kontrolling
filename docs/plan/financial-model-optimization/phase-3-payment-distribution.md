# Фаза 3: Распределение платежей

**Цель:** Реализовать связь «платёж → начисление», поддержку частичных оплат и переплат. Завершить модуль payment_distribution по ADR 0003.

**Зависимости:** Фаза 2 (архитектура баланса должна быть чистой).  
**Оценка:** 5–6 сессий (модуль строится с нуля: domain, infra, application, API, events, тесты).  
**Ветка:** `feature/fin-model-phase-3`

---

## Контекст

**Сейчас:** платёж уменьшает общий баланс FinancialSubject, но не «закрывает» конкретные начисления. Нельзя ответить на вопрос «чем оплачен членский взнос за март?».

**ADR 0003** описывает модуль `payment_distribution` с сущностями Member, PersonalAccount, PaymentDistribution и правилами приоритета. Модуль частично создан (ORM модели, начало API), но use cases распределения не завершены.

**ER-модель:** `docs/data-model/payment-distribution-erd.md` — текущая схема.

---

## Задача 3.1: Ревизия модели — устранение дублирования с PlotOwnership

### Проблема

ADR 0003 вводит `Member` (связь Owner ↔ Cooperative) и `MemberPlot` (связь Member ↔ LandPlot с долей). Но `PlotOwnership` уже хранит связь Owner ↔ LandPlot с долей и `is_primary` (= членство). Два параллельных механизма — путь к рассогласованию.

### Решение (подтверждено с владельцем проекта)

**Членство — автоматическое:** человек становится членом СТ в момент назначения ему участка. Отдельной таблицы `members` с бизнес-смыслом не нужно.

- **Member** — тонкая техническая сущность: `id`, `owner_id`, `cooperative_id`, `personal_account_id`. Создаётся автоматически при первом `PlotOwnership.is_primary = true` для данного Owner в данном Cooperative.
- **Кто является членом:** Owner, у которого есть хотя бы один `PlotOwnership.is_primary = true` в данном Cooperative (через `LandPlot.cooperative_id`). Это вычисляется, а не хранится отдельно.
- **MemberPlot — удалить.** Участки члена получаются через PlotOwnership.

### Что сделать

1. Провести ревью текущих моделей в `backend/app/modules/payment_distribution/infrastructure/models.py`:
   - Убрать `MemberPlot` (дублирует PlotOwnership).
   - Убедиться, что `Member` — тонкая сущность (owner_id + cooperative_id + ссылка на PersonalAccount).
   - Убрать поля-дубликаты PlotOwnership из `Member`.

2. Добавить в `MemberRepository` метод `get_or_create_by_ownership(owner_id, cooperative_id)` — вызывается при создании первого `PlotOwnership.is_primary = true`.

3. Обновить `docs/data-model/payment-distribution-erd.md` — убрать `member_plots`, показать связь Member → PlotOwnership.

### Файлы

```
backend/app/modules/payment_distribution/domain/entities.py
backend/app/modules/payment_distribution/infrastructure/models.py
backend/app/modules/payment_distribution/infrastructure/repositories.py  (get_or_create_by_ownership)
docs/data-model/payment-distribution-erd.md
```

---

## Задача 3.2: PersonalAccount — лицевой счёт члена

### Что это

PersonalAccount — «кошелёк» члена СТ. Платёж сначала зачисляется на лицевой счёт, затем распределяется по долгам. Переплата остаётся на лицевом счёте как аванс.

### Что сделать

**Domain** (`payment_distribution/domain/entities.py`):

```python
@dataclass
class PersonalAccount:
    id: UUID
    member_id: UUID
    cooperative_id: UUID
    account_number: str       # уникальный, человекочитаемый
    balance: Money            # текущий остаток (может быть > 0 = аванс)
    status: str               # active / closed
    opened_at: datetime
    closed_at: datetime | None = None
```

```python
@dataclass
class PersonalAccountTransaction:
    id: UUID
    account_id: UUID
    payment_id: UUID | None       # если зачисление от платежа
    distribution_id: UUID | None  # если списание в счёт долга
    transaction_number: str
    transaction_date: datetime
    amount: Money                 # + = зачисление, - = списание
    type: str                     # "credit" / "debit"
    description: str | None = None
```

**Инвариант:** `balance` = сумма всех transactions. При каждой транзакции пересчитывается (или берётся из snapshot).

**Infrastructure:** ORM модели уже частично созданы в payment_distribution. Проверить соответствие domain entity, добавить `Money` маппинг.

**Use cases:**
- `CreditAccountUseCase` — зачислить платёж на лицевой счёт (создаёт credit-транзакцию, обновляет баланс).
- `DebitAccountUseCase` — списать в счёт долга (создаёт debit-транзакцию + PaymentDistribution).

### Файлы

```
backend/app/modules/payment_distribution/domain/entities.py
backend/app/modules/payment_distribution/infrastructure/models.py
backend/app/modules/payment_distribution/application/use_cases.py
backend/app/modules/payment_distribution/infrastructure/repositories.py
```

---

## Задача 3.3: PaymentDistribution — распределение по начислениям

### Что это

Запись «из этого платежа X BYN пошли на погашение начисления Y через FinancialSubject Z».

### Domain entity

```python
@dataclass
class PaymentDistribution:
    id: UUID
    payment_id: UUID
    financial_subject_id: UUID
    accrual_id: UUID | None       # конкретное начисление (если известно)
    distribution_number: str
    distributed_at: datetime
    amount: Money
    priority: int                  # приоритет по правилу
    status: str                    # "applied" / "reversed"
```

### Бизнес-правила

1. Сумма всех distributions по payment_id ≤ payment.amount.
2. Приоритет распределения определяется `PaymentDistributionRule` (настройка СТ): сначала пени → потом самые старые долги → потом новые.
3. При отмене платежа — все distributions получают status="reversed", баланс лицевого счёта и FinancialSubject корректируется.

### Use case: DistributePaymentUseCase

**Вход:** `payment_id`, `member_id`.

**Алгоритм:**
1. Загрузить правила распределения для cooperative_id.
2. Получить список долгов (начислений с balance > 0) по FinancialSubject'ам члена, отсортированных по приоритету.
3. Для каждого долга (от высшего приоритета к низшему):
   - Списать min(остаток_платежа, сумма_долга).
   - Создать PaymentDistribution.
   - Создать debit-транзакцию на PersonalAccount.
4. Если остался неразмещённый остаток — он лежит на PersonalAccount как аванс.
5. Опубликовать события: `PaymentDistributed`, `DebtPartiallyPaid`, `DebtFullyPaid`.

### Файлы

```
backend/app/modules/payment_distribution/domain/entities.py
backend/app/modules/payment_distribution/application/use_cases.py
backend/app/modules/payment_distribution/infrastructure/repositories.py
backend/app/modules/payment_distribution/api/routes.py
backend/tests/test_api/test_payment_distribution.py
```

---

## Задача 3.4: Интеграция с модулем payments

### Проблема

Сейчас `RegisterPaymentUseCase` (payments module) создаёт Payment и публикует `PaymentConfirmed`. Но он не вызывает распределение. Нужно связать.

### Решение

**Вариант: через Domain Events.**

1. `PaymentConfirmed` event уже публикуется.
2. В `financial_core/infrastructure/event_handlers.py` уже есть `PaymentConfirmedHandler` (логирование).
3. Добавить **новый обработчик** в `payment_distribution` модуле: при получении `PaymentConfirmed` — вызвать `CreditAccountUseCase` + `DistributePaymentUseCase`.

**Важно:** обработчик работает в той же транзакции (in-process event dispatch). Если распределение не удалось — откатывается и платёж.

### Файлы

```
backend/app/modules/payment_distribution/infrastructure/event_handlers.py  (НОВЫЙ)
backend/app/modules/financial_core/infrastructure/event_handlers.py  (обновить регистрацию)
backend/app/modules/deps.py  (регистрация обработчика)
```

---

## Задача 3.5: API для распределения

### Эндпоинты

- `GET /api/v1/payment-distribution/members/{member_id}/account` — состояние лицевого счёта.
- `GET /api/v1/payment-distribution/members/{member_id}/account/transactions` — история транзакций.
- `GET /api/v1/payment-distribution/payments/{payment_id}/distributions` — как распределён конкретный платёж.
- `POST /api/v1/payment-distribution/payments/{payment_id}/distribute` — ручной запуск распределения (если автоматическое не сработало).

### Файлы

```
backend/app/modules/payment_distribution/api/routes.py
backend/app/modules/payment_distribution/application/dtos.py
```

---

## Критерий приёмки фазы 3

- [ ] `MemberPlot` удалён; связь участки↔член — через PlotOwnership.
- [ ] PersonalAccount создаётся при создании Member.
- [ ] При регистрации платежа — автоматическое зачисление на лицевой счёт и распределение по долгам.
- [ ] Частичная оплата: платёж 50 BYN при долге 100 BYN — долг уменьшается до 50, distribution = 50.
- [ ] Переплата: платёж 150 при долге 100 — долг = 0, остаток 50 на лицевом счёте.
- [ ] Отмена платежа: все distributions reversed, лицевой счёт скорректирован.
- [ ] API эндпоинты доступны и возвращают корректные данные.
- [ ] Тесты: минимум 8 сценариев (обычная оплата, частичная, переплата, отмена, несколько долгов с приоритетом, нулевой долг, пустой платёж, отмена уже отменённого).

---

*Предыдущая фаза: [phase-2-balance-architecture.md](phase-2-balance-architecture.md)*  
*Следующая фаза: [phase-4-periods-reporting.md](phase-4-periods-reporting.md)*
