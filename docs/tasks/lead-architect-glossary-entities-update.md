# Задача: обновление глоссариев и entities-minimal (Lead Architect)

**Кому:** только **Lead Architect**  
**Причина:** по правилам проекта создавать и изменять глоссарии и связанную модель данных может только Lead Architect. Остальные роли передают предложения; в репозиторий вносит он.

**Ссылки на правила:**
- [OWNERSHIP.md](../architecture/OWNERSHIP.md) — ограниченные пути, владелец `docs/architecture/glossary/`
- [glossary/README.md](../architecture/glossary/README.md) — единственный владелец глоссариев
- [.cursor/rules/architecture/architecture-rules.mdc](../../.cursor/rules/architecture/architecture-rules.mdc) — раздел «Глоссарии по доменам»

---

## Контекст

Модуль **payment_distribution** реализован (ветка `feature/payment-distribution-model`, ADR 0003). Введены сущности и термины, которых нет в глоссариях и в `entities-minimal.md`. Чтобы единый язык и документация модели не отставали от кода, нужны правки **только** от Lead Architect.

---

## 1. Обновить `docs/data-model/entities-minimal.md`

**Текущее состояние:** В блоке «Planned for later» есть пункт:
- *«Член СТ (Member) как отдельная сущность — на данный момент членство определяется через PlotOwnership.is_primary»*

**Что сделать (на усмотрение Lead Architect):**
- Убрать или переформулировать этот пункт: Member теперь реализован как отдельная сущность в модуле payment_distribution.
- При необходимости добавить в основной список сущностей (или отдельную секцию) сущности модуля payment_distribution:
  - **Member** — член СТ (связь Owner ↔ Cooperative, статус, дата вступления)
  - **PersonalAccount** — лицевой счёт члена СТ (баланс, номер счёта, статус)
  - **PersonalAccountTransaction** — операция по лицевому счёту (зачисление, списание, корректировка)
  - **PaymentDistribution** — факт распределения платежа по начислениям/долгам
  - **SettingsModule** — модуль настроек СТ (привязка к СТ)
  - **PaymentDistributionRule** — правило приоритета распределения (вид взноса, порядок)
  - **ContributionTypeSettings**, **MeterTariff** — настройки видов взносов и тарифов в рамках модуля настроек

Связи с существующими сущностями: Member → Owner, Cooperative; PersonalAccount → Member, Cooperative; PaymentDistribution → Payment (payments), PersonalAccount; и т.д. Формат таблиц и уровень детализации — на усмотрение Lead Architect.

---

## 2. Обновить глоссарии `docs/architecture/glossary/`

**Текущее состояние:** В [contributions.md](../architecture/glossary/contributions.md) есть термин «Распределение платежа». В [payments.md](../architecture/glossary/payments.md) есть ссылка на «распределение платежа, долг — contributions.md». Отдельных статей по новым терминам модуля payment_distribution нет.

**Предложения по терминам (для решения Lead Architect):**
- **Член СТ (Member)** — владелец (Owner), принятый в члены товарищества; связь Owner ↔ Cooperative с датой вступления и статусом (active / expelled / resigned). Отличается от «основного владельца участка» (PlotOwnership.is_primary): Member — явное членство в СТ с лицевым счётом.
- **Лицевой счёт (PersonalAccount)** — счёт члена СТ для учёта поступлений и распределения платежей по долгам; баланс, номер счёта, статус (active / closed / blocked).
- **Правило распределения (PaymentDistributionRule)** — настройка порядка погашения: в какую очередь списывать поступившие деньги (виды взносов, пени, счётчики).
- **Распределение платежа (PaymentDistribution)** — уже есть в contributions; при необходимости уточнить определение с учётом лицевого счёта и правил.

**Варианты действий (выбор за Lead Architect):**
- Добавить/уточнить термины в существующих файлах (payments.md, contributions.md) или
- Завести отдельный глоссарий для домена payment_distribution (например `payment_distribution.md`) и добавить его в перечень доменов в [glossary/README.md](../architecture/glossary/README.md).

---

## Чек-лист для Lead Architect

- [ ] Решить: перенос Member из «Planned for later» и объём описания сущностей payment_distribution в entities-minimal
- [ ] Внести правки в `docs/data-model/entities-minimal.md`
- [ ] Решить: один общий глоссарий или отдельный файл для payment_distribution
- [ ] Добавить/уточнить термины в `docs/architecture/glossary/`
- [ ] При новом файле глоссария — обновить перечень доменов в `docs/architecture/glossary/README.md`

---

## Кто не должен править эти артефакты

Разработчики, владельцы модулей, агенты (backend, frontend, QA и т.д.) **не коммитят** изменения в:
- `docs/architecture/glossary/`
- при необходимости — в `docs/data-model/entities-minimal.md` (если проект зафиксирует единоличное владение этим файлом за Lead Architect).

Предложения они могут передавать в виде задач (как этот файл) или в описании PR/ревью.

---

*Задача создана после ревью Architecture Guardian по модулю payment_distribution (2026-03-15).*
