# Текущий фокус: где остановились, что делать дальше

**Назначение:** Единое место, чтобы не терять контекст между сессиями. Открыл завтра → прочитал → понял, на чём остановились и что делать дальше.  
**Расположение:** `docs/plan/current-focus.md`  
**Обновлять:** в конце сессии или при смене приоритета.

---

## Зачем этот документ

- Ты (и агент) теряете контекст между сессиями.
- Здесь — одна страница с ответами: **что сейчас в работе**, **на чём остановились**, **что делать завтра**.
- Все детали и планы лежат в связанных документах по ссылкам.

---

## Канонический статус (не путать с архивом сессий ниже)

**План оптимизации финмодели** — [`financial-model-optimization/INDEX.md`](financial-model-optimization/INDEX.md): **восемь дыр из INDEX закрыты, фазы 1–5 реализованы** (зафиксировано **2026-03-22**). Сводка по коду: [`IMPLEMENTATION_SUMMARY.md`](financial-model-optimization/IMPLEMENTATION_SUMMARY.md). Критерии приёмки в [`phase-4-periods-reporting.md`](financial-model-optimization/phase-4-periods-reporting.md) и [`phase-5-debt-penalties.md`](financial-model-optimization/phase-5-debt-penalties.md) синхронизированы с этим статусом.

---

## Не дублировать: Фаза 4 — уже в коде (сессия 2026-03-22)

**Назначение:** чтобы следующий агент не делал ту же работу повторно. Детали ТЗ по-прежнему в [`phase-4-periods-reporting.md`](financial-model-optimization/phase-4-periods-reporting.md); ниже — факт реализации.

**Уже сделано (не реализовывать заново):**

| Область | Что именно |
|--------|-------------|
| Настройка СТ | Колонка `cooperatives.period_reopen_allowed_days` (дефолт 30), поле в домене/DTO/API (`CooperativeUpdate`, `CooperativeInDB`) |
| Контроль периода | `PeriodOperationGuard`, `period_auto_lock.py`; внедрение в `CreateAccrual`, `ApplyAccrual`, `CancelAccrual`, `MassCreateAccruals`, `RegisterPayment`, `CancelPayment` через `deps.get_period_operation_guard` |
| Закрытие периода | Проверка «предыдущий период не open»; при закрытии — создание `BalanceSnapshot` по всем субъектам СТ; `BalanceSnapshotModel.from_domain` пишет `balance` |
| Переоткрытие | Удаление снимков по периоду; казначей не переоткрывает `locked`; автопереход `closed`→`locked` после окна дней (список периодов, период по дате, guard, reopen); `reopen` читает дни из кооператива |
| Баланс | `GetBalanceUseCase` / `GetBalancesByCooperativeUseCase` — для даты в закрытом/заблокированном периоде отдают данные из snapshot при наличии |
| Оборотная ведомость | `IAccrualAggregateProvider` / `IPaymentAggregateProvider` — суммы за интервал дат; `GetTurnoverSheetUseCase`; `GET /api/reports/turnover` |
| Инфраструктура DI | `get_financial_period_repository` и `get_balance_snapshot_repository` подняты выше в `deps.py` (до баланса), плюс обновлённые фабрики use case |

**Интеграционные тесты фазы 4:** `backend/tests/test_api/test_financial_periods_phase4.py` (периоды, снимки, turnover, reopen/lock, блокировка начислений).

**Схема `financial_periods`:** в ORM-модели — частичный unique только для `period_type = yearly`. Схема БД поднимается из моделей при старте приложения (`create_all`), без Alembic и без переноса старых данных — при необходимости данные генерируются заново (seed и т.п.).

---

## Оптимизация финмодели — таблица статуса

| Что | Статус |
|-----|--------|
| План INDEX + 8 дыр / 5 фаз | ✅ Утверждён; реализация фаз **1–5 завершена** (2026-03-22) |
| Фаза 1: Фундамент | ✅ |
| Фаза 2: Архитектура баланса | ✅ |
| Фаза 3: Распределение платежей | ✅ (2026-03-20) |
| Фаза 4: Периоды и отчётность | ✅ (2026-03-22; тесты `test_financial_periods_phase4.py`) |
| Фаза 5: Долги и пени | ✅ (2026-03-22) |
| GitHub `main` и `docs/scenario-life-year-matrix` | ✅ Выровнены (2026-03-23): актуальный код и доки на `main`; локальные старые `feature/fin-model-phase-*` — закладки на истории, не требуют отдельного merge |

История сессий 2026-03-17 … 2026-03-20 — в архивных блоках в конце файла.

---

## Что делать в следующей сессии (после закрытия фаз)

### Ветка

Финмодель **не** требует постоянной ветки `feature/fin-model-phase-4`. Новая задача — новая ветка по `.cursor/rules/git-branch-policy.mdc`.

### Первым делом

1. Секция **«Сценарий казначейства, банковские выписки…»** — если продолжаешь матрицу года и каналы поступлений.
2. Сомнения по финмодели: [`INDEX.md`](financial-model-optimization/INDEX.md), [`IMPLEMENTATION_SUMMARY.md`](financial-model-optimization/IMPLEMENTATION_SUMMARY.md).

### Где лежит план

| Что | Путь |
|-----|------|
| INDEX (точка входа, сводка фаз) | [`docs/plan/financial-model-optimization/INDEX.md`](financial-model-optimization/INDEX.md) |
| Фаза 1: Фундамент | [`phase-1-foundation.md`](financial-model-optimization/phase-1-foundation.md) |
| Фаза 2: Архитектура баланса | [`phase-2-balance-architecture.md`](financial-model-optimization/phase-2-balance-architecture.md) |
| Фаза 3: Распределение платежей | [`phase-3-payment-distribution.md`](financial-model-optimization/phase-3-payment-distribution.md) |
| Фаза 4: Периоды и отчётность | [`phase-4-periods-reporting.md`](financial-model-optimization/phase-4-periods-reporting.md) |
| Фаза 5: Долги и пени | [`phase-5-debt-penalties.md`](financial-model-optimization/phase-5-debt-penalties.md) |

---

## Статус: ledger-ready (отдельная линия от плана фаз)

| Этап | Описание | Статус |
|------|----------|--------|
| 1–5 | Спецификация ledger-ready | ✅ Завершено, merge в main |

---

## Связанные документы (всё по плану и контексту)

| Вопрос | Документ |
|--------|----------|
| **План оптимизации финансовой модели (INDEX)** | [`docs/plan/financial-model-optimization/INDEX.md`](financial-model-optimization/INDEX.md) |
| Полная спецификация реализации (ledger-ready) | [`docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`](../tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md) |
| Анализ архитектуры и выводы | [`docs/plan/financial-architecture-analysis.md`](financial-architecture-analysis.md) |
| ADR 0002 (временная модель, ledger-ready) | [`docs/architecture/adr/0002-financial-temporal-and-ledger-ready.md`](../architecture/adr/0002-financial-temporal-and-ledger-ready.md) |
| ADR 0003 (модель распределения платежей) | [`docs/architecture/adr/0003-payment-distribution-model.md`](../architecture/adr/0003-payment-distribution-model.md) |
| Общая точка входа по проекту (Топ-5, дорожная карта) | [`docs/development-index.md`](../development-index.md) |
| План разработки и целостность (как вести задачи) | [`docs/plan/development-plan-and-integrity.md`](development-plan-and-integrity.md) |
| **ТЗ: матрица «жизнь СТ» + раннер (архив)** | [`docs/scenario/archive/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md`](../scenario/archive/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md) |
| Матрица года СТ (события, связь с модулями) | [`docs/scenario/life-year-matrix.md`](../scenario/life-year-matrix.md) |
| Файлы сценария (ЕРИП, банк — образцы) | [`docs/scenario/files/`](../scenario/files/) |

---

## Как найти этот документ завтра

- Из **индекса:** [`docs/development-index.md`](../development-index.md) → блок «Быстрые ссылки» или таблица «Когда использовать» → **Текущий фокус**.
- Из **плана:** [`docs/plan/development-plan-and-integrity.md`](development-plan-and-integrity.md) → секция 5 «Где что лежит» → строка «Где остановились / что делать завтра».
- Прямой путь: **`docs/plan/current-focus.md`**.

---

*Обновляй этот файл в конце сессии: что сделали, на каком этапе остановились, что первым делом делать в следующий раз.*

*Последнее обновление: 2026-03-22 (вечер, после коммита бэкенда) — см. блок «Конец сессии 2026-03-22 (вечер)».*

---

## Конец сессии 2026-03-22 (вечер)

- **Ветка:** `docs/scenario-life-year-matrix` — в `origin` запушены правки бэкенда (коммит с описанием в истории git).
- **Содержание коммита (кратко):** DI для `EventDispatcher` (singleton-класс), начисления — проверка финансового субъекта через репозиторий в use case’ах и связанные правки репозиториев/тестов (`backend/`).
- **Не в коммите:** локальные дампы repomix, `result_task*`, `CLAUDE_AI/` — остаются вне репозитория.

---

## Конец сессии 2026-03-22

- **Верификация по [`VERIFICATION-PROMPT.md`](financial-model-optimization/VERIFICATION-PROMPT.md):** полная заполненная таблица из 69 пунктов в репозиторий **не** внесена; при необходимости — продолжить аудит в следующей сессии или вынести итог в отдельный файл рядом с промптом.
- **Параллельный контур «сценарий жизни СТ» (матрица года, ЕРИП, файлы в `docs/scenario/`):** вести **отдельно** от основной линии разработки и **не мержить в `main`**, пока не решишь иначе. Изолировать **ветки** и при локальном запуске — **порты** (два стека не должны пересекаться при проверке работы системы). Точка входа по сценарию: [`docs/scenario/README.md`](../scenario/README.md), матрица: [`life-year-matrix.md`](../scenario/life-year-matrix.md).

---

## Сценарий казначейства, банковские выписки и завершение ревизии финмодели

**Цель:** однозначно понимать, что входит в сценарий работы казначея в «годе жизни СТ», и **не смешивать** его с отдельным контуром банковских выписок.

### Что нужно, чтобы полностью «сшить» понимание сценария казначея

1. **Явное разделение каналов поступлений** — в документации и в матрице событий зафиксировать: что относится к **ЕРИП** (примеры: `docs/scenario/files/erip-statements/`), что — к **банку** (примеры: `docs/scenario/files/bank-*-sample.csv`), и что из этого **входит в годовой сценарий**, а что — нет.
2. **Граница роли** — какие действия казначея в сценарии уже покрыты API/обработчиками (платежи, распределение, периоды), какие только описаны в `life-year-matrix.md` без реализации.
3. **Один источник правды по сценарию** — матрица [`docs/scenario/life-year-matrix.md`](../scenario/life-year-matrix.md) + при необходимости короткий README у папки `docs/scenario/files/` (что за файлы и для какого контура).
4. **Открытые вопросы к владельцу продукта (не выдумывать):** нужен ли в том же сценарии импорт/сверка **банковской выписки** или год идёт **только** через ЕРИП и ручной ввод; если банк нужен позже — вынести в отдельный эпик/матрицу.

### Отсечь банковские выписки от рабочего сценария (решение направления)

- В **операционном сценарии «год жизни СТ»** не тащить параллельный поток «импорт банковской выписки → разбор строк», пока не утверждён отдельный scope.
- Банк оставить как **отдельный трек** (док-папка, образцы CSV, будущая задача), чтобы не блокировать казначейство и финмодель смешением двух разных процессов.

### Ревизия финансовой модели по INDEX

**Закрыта:** фазы 1–5 выполнены; дальнейшие изменения — новые задачи вне этого плана (см. [`IMPLEMENTATION_SUMMARY.md`](financial-model-optimization/IMPLEMENTATION_SUMMARY.md), блок «Вне объёма фаз 1–5»).

---

## Архив: итог сессии 2026-03-20

**Фаза 3: Распределение платежей — ЗАВЕРШЕНА (100%)**

**Что сделано:**
1. ✅ Добавлены зависимости в `deps.py` (MemberRepository, PersonalAccountRepository, PaymentDistributionRepository, DebtProvider, use cases).
2. ✅ Создан `DebtProvider` — сервис для получения долгов члена СТ (accruals) с учётом частичных оплат.
3. ✅ Обновлены API routes (`/api/payment-distribution/`) — рабочие эндпоинты для просмотра счёта, транзакций, распределений и ручного запуска распределения.
4. ✅ Обновлены event handlers — `PaymentConfirmedHandler` автоматически кредитует счёт и распределяет платёж.
5. ✅ Написаны тесты (9 сценариев):
   - `test_credit_account_creates_account_and_transaction`
   - `test_credit_account_updates_existing_balance`
   - `test_credit_account_multiple_payments`
   - `test_distribute_payment_full_payment_of_single_debt`
   - `test_distribute_payment_partial_payment`
   - `test_distribute_payment_overpayment`
   - `test_distribute_payment_multiple_debts_priority`
   - `test_distribute_payment_no_debts`
   - `test_distribute_payment_zero_balance`
6. ✅ Все тесты проходят (9 passed).

**Файлы изменены/созданы:**
- `backend/app/modules/deps.py` — зависимости payment_distribution.
- `backend/app/modules/payment_distribution/infrastructure/debt_provider.py` — новый файл (DebtProvider).
- `backend/app/modules/payment_distribution/api/routes.py` — обновлены routes.
- `backend/app/modules/payment_distribution/application/use_cases.py` — добавлено списание баланса (account.debit).
- `backend/app/modules/payment_distribution/infrastructure/repositories.py` — добавлен метод `get_all`.
- `backend/app/modules/payment_distribution/tests/test_use_cases.py` — 9 тестов.

**Следующая сессия (исторически):** переход к фазе 4 — см. актуальный статус в начале файла.

---

## Архив: итог сессии 2026-03-20 (вечер) — фаза 4 начата

**Фаза 4: Финансовые периоды и отчётность — далее доведена до конца 2026-03-22 (см. канонический статус выше).**

**Что сделано:**
1. ✅ **Domain entity:**
   - `PeriodType` enum (monthly/yearly)
   - `FinancialPeriod` entity с методами close/reopen/lock
   - `BalanceSnapshot` entity
   - `FinancialSubject` и `Balance` возвращены в entities.py

2. ✅ **Репозитории (domain + infrastructure):**
   - `IFinancialPeriodRepository` интерфейс
   - `IBalanceSnapshotRepository` интерфейс
   - `FinancialPeriodRepository` реализация
   - `BalanceSnapshotRepository` реализация

3. ✅ **ORM модели:**
   - `FinancialPeriodModel` (таблица financial_periods)
   - `BalanceSnapshotModel` (таблица balance_snapshots)

4. ✅ **Миграция Alembic:**
   - `0014_add_financial_periods_and_balance_snapshots.py` (создана вручную)

5. ✅ **Use Cases:**
   - `CreateFinancialPeriodUseCase`
   - `CloseFinancialPeriodUseCase`
   - `ReopenFinancialPeriodUseCase`
   - `LockFinancialPeriodUseCase`
   - `GetFinancialPeriodsUseCase`
   - `GetFinancialPeriodByDateUseCase`

6. ✅ **API Routes:**
   - `GET /periods` — список периодов
   - `GET /periods/by-date` — период по дате
   - `POST /periods` — создать период
   - `POST /periods/{id}/close` — закрыть период
   - `POST /periods/{id}/reopen` — переоткрыть период
   - `POST /periods/{id}/lock` — заблокировать период

7. ✅ **Зависимости (deps.py):**
   - Все dependency injection функции для периодов

8. ✅ **Pydantic schemas:**
   - `FinancialPeriodCreate`, `FinancialPeriodInDB`, `FinancialPeriodClose`, `FinancialPeriodReopen`

**Файлы изменены/созданы:**
- `backend/app/modules/financial_core/domain/entities.py` — PeriodType, FinancialPeriod, BalanceSnapshot
- `backend/app/modules/financial_core/domain/repositories.py` — IFinancialPeriodRepository, IBalanceSnapshotRepository
- `backend/app/modules/financial_core/infrastructure/models.py` — FinancialPeriodModel, BalanceSnapshotModel
- `backend/app/modules/financial_core/infrastructure/repositories.py` — FinancialPeriodRepository, BalanceSnapshotRepository
- `backend/app/modules/financial_core/application/use_cases.py` — 6 use cases для периодов
- `backend/app/modules/financial_core/api/schemas.py` — schemas для периодов
- `backend/app/modules/financial_core/api/routes.py` — 6 routes для периодов
- `backend/app/modules/deps.py` — зависимости для периодов

**Чеклист после 2026-03-22 (всё закрыто):**
1. ✅ Поле `period_reopen_allowed_days` на `cooperatives` + DTO/API
2. ✅ `PeriodOperationGuard` + интеграция в accruals/payments
3. ✅ Снимки при закрытии; удаление при переоткрытии; баланс из snapshot
4. ✅ Оборотная ведомость: `GET /api/reports/turnover`
5. ✅ Интеграционные тесты API: `backend/tests/test_api/test_financial_periods_phase4.py`
6. ✅ pytest + ruff по регрессии на момент закрытия фазы

---

*Предыдущее: 2026-03-19 — план оптимизации финансовой модели из 5 фаз; ветки и Фаза 1.*

---

### Дополнение: аудит матрицы «год жизни СТ» (2026-03-20)

- Обновлён [`docs/scenario/life-year-matrix.md`](../scenario/life-year-matrix.md) **версия 0.2** — сверка EVT-001…024 с `app/main.py` и модулями по колонке «Связь».
- **Уточнения по коду:** EVT-006 → `реализовано` (смена собственника и аудит прав в `land_management`); EVT-010/EVT-013 — зафиксировано, что в `PaymentConfirmedHandler` при вызове `DistributePaymentUseCase` передаётся `debt_provider=None`, а часть эндпоинтов `payment_distribution` использует заглушку сессии `Depends(lambda: None)`; EVT-015/EVT-016 — уточнены формулировки «дыр» по фактическому API `meters`.

---

## Архив: конец сессии 2026-03-20 (конец дня)

Историческая запись. **Актуальные приоритеты** — разделы «Канонический статус» и «Что делать в следующей сессии» в начале файла.

**Дополнительно по коду (возможный техдолг вне статуса фаз):** проверить, что `DebtProvider` и сессии БД в `payment_distribution` соответствуют текущему коду (после последних сессий могло измениться).
