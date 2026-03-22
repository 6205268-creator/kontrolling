# Оптимизация финансовой модели — INDEX

**Дата плана:** 2026-03-19  
**Статус плана:** Утверждён (остаётся точкой входа и спецификацией).  
**Статус реализации:** Фазы **1–5 закрыты** (код и тесты — 2026-03-22). Сводка реализации: [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md).  
**Владелец:** Lead Architect  
**Цель:** Устранить архитектурные дыры финансовой модели, сделать её устойчивой и масштабируемой.

---

## Как пользоваться

- **Этот файл** — единственная точка входа. Читай его первым.
- **Каждая фаза** — отдельный файл. Загружай только ту фазу, над которой работаешь.
- **Фазы выполняются по порядку** (1 → 2 → 3 → 4 → 5). Внутри фазы — задачи можно параллелить, если указано.
- **После каждой фазы** — pytest, ruff, architecture check перед переходом к следующей.

---

## Сводка дыр и фаз

| # | Дыра | Влияние | Фаза | Файл |
|---|------|---------|------|------|
| 1 | Нет `due_date` на начислениях | Высокое | 1 | [phase-1-foundation.md](phase-1-foundation.md) |
| 2 | Правило баланса неполное (`created_at` не учитывается) | Среднее | 1 | [phase-1-foundation.md](phase-1-foundation.md) |
| 3 | Нет Money Value Object | Низкое | 1 | [phase-1-foundation.md](phase-1-foundation.md) |
| 4 | BalanceRepository нарушает Clean Architecture | Среднее | 2 | [phase-2-balance-architecture.md](phase-2-balance-architecture.md) |
| 5 | Нет Specification Pattern для правила баланса | Среднее | 2 | [phase-2-balance-architecture.md](phase-2-balance-architecture.md) |
| 6 | Нет связи «платёж → начисление» | Высокое | 3 | [phase-3-payment-distribution.md](phase-3-payment-distribution.md) |
| 7 | Нет финансовых периодов | Среднее | 4 | [phase-4-periods-reporting.md](phase-4-periods-reporting.md) |
| 8 | Нет модели «долга» и пеней | Среднее | 5 | [phase-5-debt-penalties.md](phase-5-debt-penalties.md) |

Все перечисленные дыры закрыты реализацией соответствующих фаз (см. [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md), [`docs/plan/current-focus.md`](../current-focus.md)).

---

## Фазы

### Фаза 1: Фундамент (низкая сложность, высокое влияние)

**Файл:** [phase-1-foundation.md](phase-1-foundation.md)  
**Что решает:** due_date, точность баланса на дату, типовая безопасность сумм.  
**Затрагивает:** accruals (domain, infra, API), financial_core (infra), shared kernel.  
**Зависимости:** нет (первая фаза).  
**Оценка:** 2–3 сессии.

### Фаза 2: Архитектура баланса (средняя сложность)

**Файл:** [phase-2-balance-architecture.md](phase-2-balance-architecture.md)  
**Что решает:** нарушение Clean Architecture в BalanceRepository, выделение правила баланса в спецификацию, подготовка к CQRS.  
**Затрагивает:** financial_core (domain, infra), accruals (infra), payments (infra).  
**Зависимости:** Фаза 1 (due_date и Money должны быть на месте).  
**Оценка:** 2–3 сессии.

### Фаза 3: Распределение платежей (средне-высокая сложность)

**Файл:** [phase-3-payment-distribution.md](phase-3-payment-distribution.md)  
**Что решает:** связь платёж → начисление, частичные оплаты, переплаты.  
**Затрагивает:** payment_distribution (весь модуль), payments, financial_core.  
**Зависимости:** Фаза 2 (баланс должен считаться правильно).  
**Оценка:** 5–6 сессий (модуль строится с нуля: domain, infra, application, API, events, тесты).

### Фаза 4: Финансовые периоды и отчётность (средняя сложность)

**Файл:** [phase-4-periods-reporting.md](phase-4-periods-reporting.md)  
**Что решает:** закрытие периодов, оборотные ведомости, снимки балансов.  
**Затрагивает:** financial_core (domain, infra), reporting.  
**Зависимости:** Фаза 2 (баланс на дату), Фаза 3 (распределение для детализации).  
**Оценка:** 2–3 сессии.

### Фаза 5: Долги и пени (высокая сложность)

**Файл:** [phase-5-debt-penalties.md](phase-5-debt-penalties.md)  
**Что решает:** долг как сущность, расчёт пеней, требования об оплате.  
**Затрагивает:** новый модуль penalties / расширение accruals + financial_core.  
**Зависимости:** Фаза 1 (due_date), Фаза 3 (распределение), Фаза 4 (периоды).  
**Оценка:** 3–4 сессии.

---

## Связь с существующими документами

| Документ | Связь |
|----------|-------|
| [ADR 0002](../../architecture/adr/0002-financial-temporal-and-ledger-ready.md) | Фаза 1 и 2 реализуют требования этого ADR |
| [ADR 0003](../../architecture/adr/0003-payment-distribution-model.md) | Фаза 3 завершает реализацию этого ADR |
| [financial-architecture-analysis.md](../financial-architecture-analysis.md) | Исходный анализ; фазы 1–2 закрывают все пункты |
| [IMPLEMENTATION_SPEC_LEDGER_READY.md](../../tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md) | Этапы 1–5 спецификации вошли в фазы 1–2 |
| [payment-distribution-erd.md](../../data-model/payment-distribution-erd.md) | ER-модель для фазы 3 |
| [project-design.md](../../project-design.md) | Фазы 4–5 расширяют секции 7–8 |

---

## Принятые решения (ревью 2026-03-19)

| # | Вопрос | Решение | Фаза |
|---|--------|---------|------|
| 1 | PersonalAccountTransaction | Оставляем полную бухгалтерскую модель | 3 |
| 2 | Платёж за закрытый период | Запретить (400); казначей переоткрывает вручную | 4 |
| 3 | BalanceParticipationRule → SQL | Translator: спецификация + автогенерация SQLAlchemy фильтра | 2 |
| 4 | `month: 0` для годового периода | Enum `PeriodType` (monthly/yearly) + `month: int \| None` | 4 |
| 5 | Snapshots при переоткрытии периода | Удалять при переоткрытии, создавать заново при закрытии | 4 |
| 6 | Data-миграция DebtLines | Не нужна — база будет чистая | 5 |
| 7 | ContributionType для пеней | Seed-запись `PENALTY` с `is_system=True` | 5 |
| 8 | BalanceSnapshot dataclass в фазе 2 | Убрать — только ADR-черновик; dataclass в фазе 4 | 2 |
| 9 | Оценка фазы 3 | Поднять до 5–6 сессий | 3 |
| 10 | Существующие ветки | Смержить аудит; payment_distribution-ветку архивировать | — |

---

## Правила работы с планом

1. **Одна фаза за раз.** Не начинать фазу N+1, пока N не пройдёт тесты и ревью.
2. **ADR перед кодом.** Если фаза требует архитектурного решения — сначала ADR, потом код.
3. **Schema First.** Диаграммы обновляются до кода (Mermaid в data-model/).
4. **Ветка на фазу.** Каждая фаза — своя git-ветка (например `feature/fin-model-phase-1`).
5. **Тесты.** Каждая задача в фазе имеет критерий приёмки с тестами.

---

*План: 2026-03-19 (ревью). Статус реализации фаз 1–5: 2026-03-22 — см. шапку документа и [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md).*
