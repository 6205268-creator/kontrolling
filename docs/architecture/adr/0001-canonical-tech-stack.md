# ADR-0001: Канонический технологический стек (FastAPI + Vue 3)

## Статус

Принято (2026-03-01).

## Контекст

Проекту необходим единый источник правды по технологиям: бэкенд, фронтенд, БД, аутентификация. В документации (docs/project-design.md) ранее были указаны Django и React; фактическая кодовая база и AGENTS.md уже используют FastAPI и Vue 3. Требовалось зафиксировать решение и устранить расхождение.

## Решение

- **Бэкенд:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic.
- **База данных:** PostgreSQL 15+ (драйвер asyncpg).
- **Фронтенд:** Vue 3, TypeScript, Vite, Pinia (SPA).
- **Аутентификация:** JWT + bcrypt (python-jose, passlib).
- **Тесты:** pytest + pytest-asyncio (backend), Vitest (frontend, по плану).
- **Линтинг:** ruff (backend), конфигурация проекта.

Каноническое описание стека — в **AGENTS.md** (раздел Tech Stack). docs/project-design.md должен совпадать с AGENTS.md по технологиям; расхождение недопустимо.

Бэкенд организован по модулям (Clean Architecture / DDD) в `backend/app/modules/`: cooperative_core, land_management, financial_core, accruals, payments, expenses, meters, reporting, administration.

## Последствия

- Все новые фичи и документация ориентируются на FastAPI и Vue 3.
- project-design.md обновлён под этот стек (задача ID-Architecture-001).
- Выбор альтернативного фреймворка (Django, React и т.п.) потребует нового ADR и явного обоснования.

## Ссылки

- AGENTS.md (Tech Stack, Architecture)
- docs/project-design.md (раздел 2 — Технологический стек)
- docs/history/DECISIONS_LOG.md (DEC-002)
