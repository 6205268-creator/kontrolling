# Анализ архитектурной спецификации «Ledger-ready MVP»

**Дата:** 2026-03-04  
**Источник:** Текст архитектурной цели (временная модель, необратимость, баланс на дату, подготовка к ledger).

---

## 1. Выводы по текущему состоянию кода

### 1.1. Что уже есть

| Требование | Статус в коде | Комментарий |
|------------|----------------|-------------|
| **created_at** | ✅ Есть | Accrual, Payment, Expense — в моделях и домене. В части миграций nullable — стоит зафиксировать NOT NULL. |
| **Экономическая дата** | ✅ Есть под другими именами | `accrual_date` (Accrual), `payment_date` (Payment) — по смыслу это Event Time. Отдельный столбец `event_date` не обязателен, если зафиксировать роль в ADR и в правиле баланса. |
| **status (cancelled)** | ✅ Есть | `status = "cancelled"` для Accrual, Payment, Expense. |
| **Расчёт баланса** | ✅ Есть, но без времени | `BalanceRepository.calculate_balance(financial_subject_id)` считает сумму applied accruals и confirmed payments. Нет параметра `as_of_date`, нет правила по event_date/created_at/cancelled_at. |
| **BalanceCalculator** | ✅ Есть | `financial_core.domain.services.BalanceCalculator` — чистая формула (total_accruals - total_payments). Не используется в репозитории для временного правила. |
| **Cancel в use case** | ✅ Есть | Реализовано в application layer: `CancelPaymentUseCase`, `CancelAccrualUseCase`, `CancelExpenseUseCase` — просто меняют `status = "cancelled"`. |

### 1.2. Чего не хватает

| Требование | Где | Что сделать |
|------------|-----|-------------|
| **cancelled_at** | Accrual, Payment, Expense | Добавить столбец (datetime, nullable), заполнять при отмене. |
| **cancelled_by_user_id** | Accrual, Payment, Expense | Добавить столбец (UUID, nullable), передавать в cancel из API. |
| **cancellation_reason** | Accrual, Payment, Expense | Добавить столбец (text, nullable), опционально в API. |
| **operation_number** | Accrual, Payment (и при необходимости Expense) | Уникальный человекочитаемый номер (например, генерация по cooperative + год + порядковый номер). |
| **Правило баланса на дату** | BalanceRepository, домен | Участие операции в балансе на дату X: event_date ≤ X, created_at ≤ X, (status ≠ cancelled OR cancelled_at > X). Реализовать в одном месте (сервис/репозиторий). |
| **Контракт баланса с as_of_date** | IBalanceRepository, API | Сигнатура `calculate(financial_subject_id, as_of_date: date | None) -> Money`; пока можно вызывать с `as_of_date=None` как «текущий баланс». |
| **Cancel в домене** | Payment, Accrual (и при желании Expense) | Метод `entity.cancel(cancelled_by, reason, now)` в сущности; use case только вызывает его и сохраняет. |
| **Защита amount** | Домен, при необходимости ORM | В домене не давать setter на amount после создания; при update в репозитории не обновлять amount. |
| **Domain Events** | Accrual, Payment | При подтверждении/отмене генерировать события (PaymentConfirmed, PaymentCancelled, AccrualApplied, AccrualCancelled); пока можно только логировать или держать в памяти. |
| **FinancialEntry (проектирование)** | ADR / глоссарий | Описать сущность и путь перехода к ledger через события — без реализации в БД. |

---

## 2. Оценка совета

- **Стратегия «ledger-ready, но не ledger-heavy»** — уместна: не тянем двойную запись и event sourcing, но закрываем временную модель и необратимость.
- **Две оси времени (Event Time / System Time)** — необходимы для баланса на дату и отчётов; без них «баланс на конец месяца» неоднозначен.
- **Append-only и компенсирующие операции** — соответствуют практике учёта и снижают риски манипуляций.
- **Rich Domain для cancel** — правильно: инварианты (не отменить дважды, выставить cancelled_at) держать в одном месте.
- **BalanceCalculator как отдельный сервис** — уже есть в виде доменного сервиса; нужно довести использование до единой точки расчёта с временным правилом и контрактом с `as_of_date`.
- **Не делать сейчас: event sourcing, план счетов, двойная запись** — разумно для MVP.

---

## 3. Предложения по приоритетам

### Фаза 1 (минимальный набор для временной корректности)

1. **Модель данных**
   - Добавить в Accrual, Payment (и при желании Expense): `cancelled_at`, `cancelled_by_user_id`, `cancellation_reason`, `operation_number`.
   - Убедиться, что `created_at` NOT NULL везде.

2. **Правило баланса**
   - Формализовать в коде правило участия в балансе на дату X (event_date ≤ X, created_at ≤ X, не отменена или cancelled_at > X).
   - Ввести контракт `calculate(financial_subject_id, as_of_date=None)`; реализация в BalanceRepository или в отдельном сервисе, использующем BalanceCalculator для формулы.

3. **ADR**
   - Принять и зафиксировать ADR (например, 0002): временная модель, правило баланса, перечень полей, запрет изменения amount и восстановления отмены.

### Фаза 2 (домен и аудит)

4. **Cancel в сущности**
   - Перенести отмену в `Payment.cancel(...)` и `Accrual.cancel(...)` (и при необходимости Expense); use case только загружает, вызывает cancel, сохраняет.

5. **Защита amount**
   - В домене убрать возможность изменения amount после создания; в репозитории при update не обновлять amount (и при необходимости зафиксировать в ORM).

6. **operation_number**
   - Реализовать генерацию и уникальность; использовать в API ответах и при необходимости в печатных формах.

### Фаза 3 (заготовка под ledger)

7. **Domain Events**
   - Ввести типы событий PaymentConfirmed, PaymentCancelled, AccrualApplied, AccrualCancelled; вызывать их при соответствующих действиях; пока только логирование/память.

8. **FinancialEntry**
   - Описать в ADR (и при необходимости в глоссарии) структуру и сценарий перехода к ledger через события, без реализации таблиц.

---

## 4. Риски, если не внедрять

- **Баланс на дату** — без event_date/created_at/cancelled_at нельзя однозначно считать баланс на конец прошлого месяца или на произвольную дату.
- **Аудит отмен** — без cancelled_at/cancelled_by/reason сложнее обосновывать корректность перед проверяющими.
- **Манипуляции** — возможность менять amount или «вернуть» отмену увеличивает риски искажения учёта.
- **Переход к ledger** — без единого правила участия в балансе и без заготовки событий переход к полноценному учёту потом потребует более болезненного рефакторинга.

---

## 5. Итоговая позиция

Спецификацию стоит принять как целевую архитектурную позицию. Изменения не усложняют MVP сверх меры, но дают:

- временную корректность баланса;
- необратимость и прозрачность отмен;
- задел под баланс на дату и отчёты;
- путь к ledger без переписывания домена.

Рекомендуется зафиксировать решение в ADR (черновик уже подготовлен: `docs/architecture/adr/0002-financial-temporal-and-ledger-ready.md`), после чего выполнять по фазам выше с приоритетом Фазы 1.

---

## 6. Связь с документами проекта

| Документ | Действие |
|----------|-----------|
| `docs/development-index.md` | После принятия ADR — добавить 0002 в индекс ADR; при появлении задач — включить в Топ-5 или в задания по командам. |
| `docs/plan/development-plan-and-integrity.md` | Упомянуть временную модель и ledger-ready в разделе целостности (опционально). |
| `docs/architecture/system-patterns.md` | Добавить подраздел «Временная модель финансов» и ссылку на ADR 0002. |
| `docs/architecture/glossary/financial.md` | Ввести/уточнить термины: Event Time, System Time, operation_number, правило участия в балансе (по согласованию с Lead Architect). |
