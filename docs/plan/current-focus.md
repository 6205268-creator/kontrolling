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

## Текущая приоритетная задача (обновлено 2026-03-19)

### Название

**Оптимизация финансовой модели** — устранение архитектурных дыр, 5 фаз от фундамента до долгов и пеней.

### Статус

| Что | Статус |
|-----|--------|
| План оптимизации (5 фаз, INDEX + детальные файлы) | ✅ Готов, утверждён |
| Фаза 1: Фундамент (due_date, баланс, Money VO) | ⚪ Следующая к выполнению |
| Фаза 2: Архитектура баланса | ⚪ Ожидает (зависит от Фазы 1) |
| Фаза 3: Распределение платежей | ⚪ Ожидает (зависит от Фазы 2) |
| Фаза 4: Финансовые периоды и отчётность | ⚪ Ожидает |
| Фаза 5: Долги и пени | ⚪ Ожидает |
| Старые ветки (audit, payment_distribution) | 🟡 Решение: смержить аудит, архивировать payment_distribution |

### На чём остановились

**Итог сессии 2026-03-19 (планирование):**

- Проведён анализ финансовой модели, выявлены 8 архитектурных дыр.
- Составлен и утверждён **план оптимизации из 5 фаз** — [`docs/plan/financial-model-optimization/INDEX.md`](financial-model-optimization/INDEX.md).
- Каждая фаза описана в отдельном файле (задачи, критерии приёмки, затрагиваемые модули).
- Принято 10 архитектурных решений (см. INDEX, секция «Принятые решения»).
- Код не менялся — сессия была полностью посвящена планированию.

**Ранее (итог сессии 2026-03-17):**

- По аудиту (`docs/tasks/TASK_audit_fixes_20260317.md`): части 1, 2 и 3 выполнены. Ветка `feature/audit-fixes-20260317`.
- Ветка `feature/2026-03-15-session`: payment_distribution заготовка, ADR 0003, правки API/фронт.

---

## Что делать завтра (или в следующей сессии)

### Ветка

- **Создать новую ветку** `feature/fin-model-phase-1` от main для Фазы 1.
- **Старые ветки:** `feature/audit-fixes-20260317` — смержить в main (решение #10); `feature/2026-03-15-session` (payment_distribution) — архивировать (будет переделана в Фазе 3).
- **Правило:** `.cursor/rules/git-branch-policy.mdc` — не коммитить в main, не мержить без одобрения.

### Задача на завтра (первым делом)

1. **Открыть** `docs/plan/current-focus.md` — убедиться в контексте.
2. **Разобраться со старыми ветками** (merge аудита в main, архивация payment_distribution) — по команде.
3. **Начать Фазу 1** оптимизации финансовой модели:
   - Читать: [`docs/plan/financial-model-optimization/phase-1-foundation.md`](financial-model-optimization/phase-1-foundation.md)
   - Задачи: добавить `due_date` на начисления, исправить правило баланса, создать Money Value Object.
   - Оценка: 2–3 сессии.

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

## Статус по этапам (обновлять по ходу)

**Ledger-ready (завершён, в main):**

| Этап | Описание | Статус |
|------|----------|--------|
| 1–5 | Ledger-ready спецификация | ✅ Завершено, merge в main |

**Оптимизация финансовой модели:**

| Фаза | Описание | Оценка | Статус |
|------|----------|--------|--------|
| 1 | Фундамент (due_date, баланс, Money VO) | 2–3 сессии | ⚪ Следующая |
| 2 | Архитектура баланса (Clean Arch, Specification) | 2–3 сессии | ⚪ Ожидает |
| 3 | Распределение платежей (модуль с нуля) | 5–6 сессий | ⚪ Ожидает |
| 4 | Финансовые периоды и отчётность | 2–3 сессии | ⚪ Ожидает |
| 5 | Долги и пени | 3–4 сессии | ⚪ Ожидает |

**Старые ветки:**

| Ветка | Что | Решение |
|-------|-----|---------|
| `feature/audit-fixes-20260317` | Аудит (части 1–3) | Смержить в main |
| `feature/2026-03-15-session` | payment_distribution заготовка | Архивировать (переделка в Фазе 3) |

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
| **ТЗ: матрица «жизнь СТ» + раннер (для отдельной сессии)** | [`docs/scenario/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md`](../scenario/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md) |

---

## Как найти этот документ завтра

- Из **индекса:** [`docs/development-index.md`](../development-index.md) → блок «Быстрые ссылки» или таблица «Когда использовать» → **Текущий фокус**.
- Из **плана:** [`docs/plan/development-plan-and-integrity.md`](development-plan-and-integrity.md) → секция 5 «Где что лежит» → строка «Где остановились / что делать завтра».
- Прямой путь: **`docs/plan/current-focus.md`**.

---

*Обновляй этот файл в конце сессии: что сделали, на каком этапе остановились, что первым делом делать в следующий раз.*

*Последнее обновление: 2026-03-20 — добавлено ТЗ на матрицу года жизни СТ и будущий раннер: [`docs/scenario/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md`](../scenario/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md) (передача контекста в новую сессию). Приоритет по коду без изменений: финмодель Фаза 1.*

*Предыдущее: 2026-03-19 — план оптимизации финансовой модели из 5 фаз; ветки и Фаза 1.*
