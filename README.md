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
│   ├── architecture/            # Архитектурные диаграммы
│   ├── source-material/         # Исходные материалы
│   └── processes/               # BPMN-процессы
└── README.md
```

## Инструменты разработки (AI / Cursor)

- **[Context7](https://github.com/upstash/context7)** — MCP-сервер для актуальной документации библиотек (FastAPI, SQLAlchemy, Vue и др.). Подключён в проекте (`.cursor/mcp.json`); ассистенты должны **всегда** использовать Context7 при запросах по API и примерам кода библиотек. [Получить ключ](https://context7.com/dashboard) (опционально, для повышенных лимитов).

## Документация

**Единая точка входа:** [Индекс разработки](docs/development-index.md) — Топ-5 задач, дорожная карта, архитектура, роли агентов.

- [Дизайн системы](docs/project-design.md)
- [План реализации](docs/project-implementation.md)
- [Модель данных](docs/data-model/schema-viewer.html)
- [Политика окружений и переменных](docs/architecture/environment-policy.md) — local dev, CI, production; где лежит .env, запуск backend из `backend/`.

---

## 🔀 Параллельный проект: Интерактивное руководство сценариев

> **Важно:** Этот проект развивается **параллельно** в отдельном репозитории и **не конфликтует** с основной разработкой.

### 📍 Расположение

```
kontrolling/
└── kontrolling-scenarios/    # Отдельный Vue 3 проект
    ├── src/
    ├── public/
    ├── package.json
    └── README.md
```

### 🎯 Назначение

**Интерактивное руководство СТ «Дружное»** — визуализация жизненных сценариев садоводческого товарищества для:

- **Сбора обратной связи** от реальных казначеев и председателей
- **Сценарного тестирования** backend и frontend
- **Документирования требований** к новым функциям
- **Приоритизации бэклога** на основе реальных ситуаций

### 📊 Что внутри

| Компонент | Описание |
|-----------|----------|
| **72 события** | Хронология года СТ: 15 разделов (январь–декабрь) |
| **12 выписок ЕРИП** | Реальные банковские платежи с детализацией |
| **Персонажи** | Председатель, казначей, 14 владельцев участков |
| **Бэклог** | 14 функций с приоритетами (High/Medium/Low) |
| **Статусы** | ✅ Реализовано / ⚠️ Частично / ❌ Не реализовано / 🔍 На пересмотр |

### 🚀 Запуск

```bash
cd kontrolling-scenarios
npm install
npm run dev
```

**Порт:** http://localhost:5175 (не конфликтует с основным проектом на 5173)

### 🔗 Связь с основным проектом

Этот проект **не является частью основного репозитория** и развивается отдельно:

- **Отдельный Git репозиторий** в папке `kontrolling-scenarios/`
- **Отдельный стек:** Vue 3 + Vite + Pinia + Tailwind
- **Отдельный порт:** 5175 (основной проект — 5173)
- **Отдельная сборка:** `npm run build` → `dist/`

**Интеграция:** В будущем сценарии будут использоваться как источник требований для новых фич в основном проекте через:
- Ссылки на события в task-трекере
- Автоматическую генерацию тест-кейсов
- Валидацию реализованных функций

### 📚 Документация

- [README](kontrolling-scenarios/README.md) — описание проекта
- [DEPLOY](kontrolling-scenarios/DEPLOY.md) — развёртывание и хостинг

---
