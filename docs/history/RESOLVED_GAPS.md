# Устранённые архитектурные дыры

## 15 непроходящих тестов блокировали production-ready

- **Дата устранения**: 2026-03-10
- **Команда**: Backend
- **Результат**: Исправлены все 15 непроходящих тестов:
  - MeterRepository: добавлен `get_all(cooperative_id)` для multitenancy
  - MeterReadingRepository: реализованы все методы `IRepository` (get_by_id, get_all, update, delete)
  - Land plots: исправлена генерация UUID для ownerships, delete для admin, financial_subject_id в ответе
  - Reports: изменена ассерция 400 → 422 для невалидного UUID
- **Верификация**: 176 тестов прошли, 5 skipped; ruff check: 0 ошибок; architecture linter: все проверки пройдены; seed_db: данные создаются без ошибок

---

## Источник правды для технологического стека

- **Дата устранения**: 2026-03-01
- **Команда**: Architecture
- **Файл-задание**: [TASK_Architecture_20260301.md](../tasks/TASK_Architecture_20260301.md)
- **Результат**: В AGENTS.md и docs/project-design.md зафиксирован стек: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 15+ (asyncpg), Vue 3 + TypeScript + Vite + Pinia
- **Верификация**: AGENTS.md обновлён, project-design.md синхронизирован с фактической реализацией

## Источник правды для размещения ORM-моделей

- **Дата устранения**: 2026-03-01
- **Команда**: Backend
- **Файл-задание**: [TASK_Backend_20260301.md](../tasks/TASK_Backend_20260301.md)
- **Результат**: Зафиксировано, что ORM-модели размещаются в `modules/*/infrastructure/models.py`, регистрация через `db/register_models.py`; seed-скрипты импортируют из модулей
- **Верификация**: seed_db.py использует импорты из `app.modules.<module>.infrastructure.models`, документация обновлена

## Границы слоёв: зависимость API от Infrastructure

- **Дата устранения**: 2026-03-01
- **Команда**: Backend
- **Файл-задание**: [TASK_Backend_20260301.md](../tasks/TASK_Backend_20260301.md)
- **Результат**: Зафиксировано правило: Presentation слой не импортирует из Infrastructure напрямую; тип AppUser берётся из domain entities, маппинг ORM→domain выполняется внутри модуля
- **Верификация**: app.api.deps использует тип из domain, загрузка через repository модуля administration

## Роли окружений и политика переменных

- **Дата устранения**: 2026-03-01
- **Команда**: DevOps
- **Файл-задание**: [TASK_DevOps_20260301.md](../tasks/TASK_DevOps_20260301.md)
- **Результат**: Создан документ docs/architecture/environment-policy.md с описанием окружений (dev/stage/prod), переменных окружения и политики безопасности
- **Верификация**: Документ существует, все переменные задокументированы

## Расположение .env и рабочий каталог

- **Дата устранения**: 2026-03-01
- **Команда**: DevOps
- **Файл-задание**: [TASK_DevOps_20260301.md](../tasks/TASK_DevOps_20260301.md)
- **Результат**: Зафиксировано в AGENTS.md: запуск backend только из `backend/`, config читает `.env` относительно CWD
- **Верификация**: AGENTS.md обновлён, docker-compose и документация синхронизированы

## Каноничность get_db и переопределение в тестах

- **Дата устранения**: 2026-03-01
- **Команда**: Backend
- **Файл-задание**: [TASK_Backend_20260301.md](../tasks/TASK_Backend_20260301.md)
- **Результат**: Зафиксировано: каноническая точка — `app.api.deps.get_db`; в тестах переопределяется через `test_db` fixture в conftest.py
- **Верификация**: 197 тестов проходят, conftest.py корректно подменяет сессию

## ADR: индекс и процесс ведения

- **Дата устранения**: 2026-03-01
- **Команда**: Architecture
- **Файл-задание**: [TASK_Architecture_20260301.md](../tasks/TASK_Architecture_20260301.md)
- **Результат**: Создан docs/architecture/adr/README.md с индексом и процессом ведения ADR; зафиксирован формат и ответственный
- **Верификация**: ADR-индекс существует, процесс описан

## Канонический seed и скрипты наполнения

- **Дата устранения**: 2026-03-01
- **Команда**: Backend
- **Файл-задание**: [TASK_Backend_20260301.md](../tasks/TASK_Backend_20260301.md)
- **Результат**: Зафиксировано в AGENTS.md: единственный канонический entry point — `python -m app.scripts.seed_db` из backend/; скрипт идемпотентен
- **Верификация**: seed_db.py работает корректно, docker-compose использует эту команду

## CI и переменные для тестов

- **Дата устранения**: 2026-03-01
- **Команда**: DevOps
- **Файл-задание**: [TASK_DevOps_20260301.md](../tasks/TASK_DevOps_20260301.md)
- **Результат**: Задокументировано в AGENTS.md: backend tests используют in-memory SQLite через conftest.py, DATABASE_URL не требуется в CI
- **Верификация**: GitHub Actions workflow backend-tests.yml проходит без DATABASE_URL, 197 тестов

## Глоссарии по доменам

- **Дата устранения**: 2026-03-10
- **Команда**: Architecture
- **Результат**: Заполнены глоссарии для всех 10 доменов: cooperative, land, payments, expenses, meters, reporting, administration (ранее были заполнены accruals, contributions, financial). Формат и стиль — по образцу существующих; термины взяты из domain/entities, use_cases и project-design.
- **Верификация**: Файлы в `docs/architecture/glossary/` (cooperative.md, land.md, payments.md, expenses.md, meters.md, reporting.md, administration.md) содержат таблицы терминов и примеры использования в СТ.
