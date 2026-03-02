# Глоссарии доменов

Единый язык (Ubiquitous Language) по доменам проекта Controlling.

---

## ⚠️ Важно: единственный владелец

**Создавать и изменять файлы в этом каталоге может только Lead Architect.** Ни разработчики, ни владельцы модулей, ни агенты (backend, frontend, QA и т.д.) не вносят правки в глоссарии напрямую. Предложения по терминам передаются Lead Architect; в репозиторий меняет только он.

Если глоссарии начнут править все кому не лень, единый язык разъезжается и проект теряет один источник правды. Это правило зафиксировано с самого старта, чтобы такого не допустить. Подробнее: `.cursor/rules/architecture/architecture-rules.mdc`, раздел «Глоссарии по доменам»; полный список ограниченных путей: [docs/architecture/OWNERSHIP.md](../OWNERSHIP.md).

---

## Перечень доменов и файлов

| Домен | Файл | Примечание |
|-------|------|------------|
| cooperative | [cooperative.md](cooperative.md) | СТ, настройки товарищества |
| land | [land.md](land.md) | Участки, владельцы, PlotOwnership |
| financial | [financial.md](financial.md) | FinancialSubject, балансы |
| accruals | [accruals.md](accruals.md) | Начисления, виды взносов |
| payments | [payments.md](payments.md) | Платежи, регистрация оплат |
| expenses | [expenses.md](expenses.md) | Расходы СТ |
| meters | [meters.md](meters.md) | Приборы учёта, показания |
| reporting | [reporting.md](reporting.md) | Отчётность |
| administration | [administration.md](administration.md) | Пользователи, роли, аудит |

Дополнительно: [contributions.md](contributions.md) — взносы, долг, пени, тарифы (смежный с accruals).

## Ответственность (единственный владелец)

**Только Lead Architect** создаёт и актуализирует файлы в `docs/architecture/glossary/`. Другие роли и агенты не изменяют глоссарии; предложения передаются архитектору. Полная политика: `.cursor/rules/architecture/architecture-rules.mdc` (раздел «Глоссарии по доменам»).
