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

## Текущая приоритетная задача (на 2026-03-04)

### Название

**Ledger-ready MVP** — временная модель финансов, необратимость операций, баланс на дату, подготовка к возможному переходу на ledger (без внедрения двойной записи и event sourcing).

### Статус

| Что | Статус |
|-----|--------|
| Архитектурное решение (ADR 0002) | ✅ Черновик готов, предложено |
| Анализ и выводы | ✅ Готово |
| Пошаговая спецификация для реализации | ✅ Готово |
| **Реализация в коде** | ⬜ **Не начата** |

### На чём остановились

- Сформулирована архитектурная цель (временная модель Event Time / System Time, правило баланса на дату, отмена через домен, защита amount, domain events).
- Написан анализ: [`docs/plan/financial-architecture-analysis.md`](financial-architecture-analysis.md) — что есть в коде, чего не хватает, риски, фазы.
- Зафиксирован черновик ADR: [`docs/architecture/adr/0002-financial-temporal-and-ledger-ready.md`](../architecture/adr/0002-financial-temporal-and-ledger-ready.md).
- Подготовлена **пошаговая спецификация для агента** со всеми изменениями по файлам и тестам: [`docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`](../tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md). В ней 5 этапов (модель данных → правило баланса → отмена в домене → защита amount → domain events). Реализацию **не начинали**.

**Конец сессии 2026-03-04:** на сегодня работу завершаем; реализация не начиналась. Завтра — с Этапа 1 по спецификации.

---

## Что делать завтра (или в следующей сессии)

### Ветка для задачи

- **Имя ветки:** `feature/ledger-ready-mvp`
- **Правило:** агент следует `.cursor/rules/git-branch-policy.mdc`
  - Не коммитить в main/master
  - Не выполнять merge без явного одобрения
  - Если ветка не существует — спросить перед созданием
  - Если существует — проверить статус (`git status`, `git log -n 5`) и сообщить пользователю

### Порядок работы

1. **Открыть этот файл:** `docs/plan/current-focus.md` — ты здесь.
2. **Открыть спецификацию:** [`docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`](../tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md).
3. **Сказать агенту (backend-developer):**
   *«Реализуй по шагам спецификацию из `docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`. Используй роль backend-developer. Выполняй этапы строго по порядку (1 → 2 → … → 5). После каждого этапа запускай проверки в порядке:*
   - *`pytest` (все тесты зелёные)*
   - *`ruff check .` и `ruff format --check .` (без ошибок)*
   - *`python -m app.scripts.architecture_linter` (exit code 0)*
   - *`python -m app.scripts.seed_db` (без ошибок)*
   - *Вызвать @architecture-guardian для ревью по модулям*
   - *Мелкие ошибки исправлять сразу, серьёзные — после подтверждения пользователя.*
   *Не смешивать слои.»*
4. **Начать с Этапа 1** — миграция и новые поля (cancelled_at, cancelled_by_user_id, cancellation_reason, operation_number) в Accrual, Payment, Expense.

После выполнения каждого этапа можно обновлять секцию «Статус по этапам» ниже.

---

## Статус по этапам (обновлять по ходу)

| Этап | Описание | Статус |
|------|----------|--------|
| 1 | Модель данных — новые поля, миграция, operation_number | ⬜ Не начат |
| 2 | Правило баланса на дату, контракт as_of_date | ⬜ Не начат |
| 3 | Отмена в домене (entity.cancel), API с причиной/пользователем | ⬜ Не начат |
| 4 | Защита amount (не обновлять при update) | ⬜ Не начат |
| 5 | Domain events (заготовка, логирование) | ⬜ Не начат |

---

## Связанные документы (всё по плану и контексту)

| Вопрос | Документ |
|--------|----------|
| **Полная спецификация реализации** (файлы, тесты, этапы) | [`docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`](../tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md) |
| Анализ архитектуры и выводы | [`docs/plan/financial-architecture-analysis.md`](financial-architecture-analysis.md) |
| ADR 0002 (временная модель, ledger-ready) | [`docs/architecture/adr/0002-financial-temporal-and-ledger-ready.md`](../architecture/adr/0002-financial-temporal-and-ledger-ready.md) |
| Общая точка входа по проекту (Топ-5, дорожная карта) | [`docs/development-index.md`](../development-index.md) |
| План разработки и целостность (как вести задачи) | [`docs/plan/development-plan-and-integrity.md`](development-plan-and-integrity.md) |
| Где что лежит (таблица) | Секция 5 в [`development-plan-and-integrity.md`](development-plan-and-integrity.md) |

---

## Как найти этот документ завтра

- Из **индекса:** [`docs/development-index.md`](../development-index.md) → блок «Быстрые ссылки» или таблица «Когда использовать» → **Текущий фокус**.
- Из **плана:** [`docs/plan/development-plan-and-integrity.md`](development-plan-and-integrity.md) → секция 5 «Где что лежит» → строка «Где остановились / что делать завтра».
- Прямой путь: **`docs/plan/current-focus.md`**.

---

*Обновляй этот файл в конце сессии: что сделали, на каком этапе остановились, что первым делом делать в следующий раз.*
