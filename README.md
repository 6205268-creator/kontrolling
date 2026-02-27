# КОНТРОЛЛИНГ — Система управления СТ (РБ)

Система учёта хозяйственной деятельности садоводческих товариществ (СТ) Республики Беларусь.

[![Backend tests](https://github.com/OWNER/kontrolling/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/OWNER/kontrolling/actions/workflows/backend-tests.yml)
[![Frontend tests](https://github.com/OWNER/kontrolling/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/OWNER/kontrolling/actions/workflows/frontend-tests.yml)

> В бейджах замените `OWNER` на владельца репозитория (логин или организацию GitHub).

## Стек

| Слой | Технология |
|------|-----------|
| Backend | Python 3.11 + FastAPI |
| БД | PostgreSQL 15+ + SQLAlchemy 2.0 (async) + Alembic |
| Frontend | Vue 3 + TypeScript + Vite + Pinia |
| Auth | JWT + bcrypt |
| Тесты | pytest + Vitest |

## Структура проекта

```
kontrolling/
├── backend/            # FastAPI приложение
├── frontend/           # Vue 3 SPA
├── docs/
│   ├── project-design.md        # Архитектура и дизайн системы
│   ├── project-implementation.md # План реализации (35 фич)
│   ├── decomposition.md         # Декомпозиция модулей
│   ├── data-model/              # Модель данных (диаграммы)
│   ├── architecture/            # C4-диаграммы
│   ├── source-material/         # Исходные материалы
│   └── processes/               # BPMN-процессы
└── README.md
```

## Инструменты разработки (AI / Cursor)

- **[Context7](https://github.com/upstash/context7)** — MCP-сервер для актуальной документации библиотек (FastAPI, SQLAlchemy, Vue и др.). Подключён в проекте (`.cursor/mcp.json`); ассистенты должны **всегда** использовать Context7 при запросах по API и примерам кода библиотек. [Получить ключ](https://context7.com/dashboard) (опционально, для повышенных лимитов).

## Документация

- [Дизайн системы](docs/project-design.md)
- [План реализации](docs/project-implementation.md)
- [Модель данных](docs/data-model/schema-viewer.html)
