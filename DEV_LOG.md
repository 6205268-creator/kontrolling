# Лог разработки системы учёта СНТ

Все существенные действия по проекту фиксируются в этом файле: созданные папки/файлы, установленные зависимости, выполненные команды.

## 2026-01-20

- Создан файл `DEV_LOG.md` для фиксации истории разработки.
- Принято решение использовать стек `FastAPI + SQLAlchemy + PostgreSQL` для нового backend ядра учёта СНТ.
- Существующий Node.js backend и фронтенд не трогаются; для ядра учёта будет создан отдельный Python‑backend.

### Backend ядра учёта СНТ

- Создана папка `backend_snt_core` для Python‑backend ядра учёта СНТ.
- Добавлен файл `backend_snt_core/README.md` с описанием назначения backend ядра.
- Добавлен файл `backend_snt_core/requirements.txt` со списком Python‑зависимостей:
  - `fastapi`
  - `uvicorn[standard]`
  - `SQLAlchemy`
  - `psycopg[binary]`
  - `alembic`
  - `pydantic`
  - `pydantic-settings`.
- Создана базовая структура приложения FastAPI:
  - `backend_snt_core/app/main.py` — точка входа FastAPI с простым `GET /health`.
  - `backend_snt_core/app/config.py` — настройки через `pydantic-settings` (переменная `DATABASE_URL` из `.env`).
  - `backend_snt_core/app/db/base.py` — `Base = declarative_base()` для моделей SQLAlchemy.
  - `backend_snt_core/app/db/session.py` — создание `engine`, `SessionLocal` и зависимости `get_db()`.
- Создан файл `ARCHITECTURE_SNT_CORE.md` с подробным описанием архитектуры ядра учёта (схема данных, документы, регистры, алгоритмы проведения/отмены) в формате, удобном для Obsidian.
- Создано виртуальное окружение Python:
  - команда: `python -m venv .venv` (из корня проекта).
- Установлены зависимости для backend ядра в виртуальное окружение:
  - команда (из корня проекта): `.venv\Scripts\pip install fastapi uvicorn[standard] SQLAlchemy psycopg[binary] alembic pydantic pydantic-settings`.
  - Успешно установлены версии (на момент установки): `fastapi-0.128.0`, `SQLAlchemy-2.0.45`, `alembic-1.18.1`, `pydantic-2.12.5`, `pydantic-settings-2.12.0`, `uvicorn-0.40.0`, `psycopg-3.3.2` и связанные зависимости.

### Очистка проекта от Telegram/Frontend

- Удалены старые каталоги:
  - `frontend/`
  - `backend/` (Node.js / Telegram).
- Обновлён корневой `README.md`: удалены инструкции по Telegram, описано ядро учёта СНТ и запуск FastAPI.

### Миграции и базовая модель данных

- Инициализирован Alembic для миграций:
  - команда: `.venv\Scripts\alembic -c backend_snt_core\alembic.ini init backend_snt_core\alembic`.
- Настроен Alembic `backend_snt_core/alembic/env.py`:
  - подключение метаданных SQLAlchemy моделей (`Base.metadata`);
  - чтение `DATABASE_URL` из переменных окружения (или fallback на `alembic.ini`).
- Добавлена стартовая миграция схемы БД:
  - `backend_snt_core/alembic/versions/0001_init_schema.py` (таблицы: `snt`, `plot`, `owner`, `plot_owner`, `charge_item`, `doc_accrual`, `doc_accrual_row`, `doc_payment`, `doc_payment_row`, `reg_balance` + FK/CHECK/индексы).
- Добавлены SQLAlchemy модели таблиц в `backend_snt_core/app/models/`.

### REST API и проведение

- Добавлены маршруты REST API:
  - `POST/GET /snts`
  - `POST/GET /snts/{snt_id}/plots`
  - `POST/GET /snts/{snt_id}/owners`
  - `POST/GET /snts/{snt_id}/charge-items`
  - `POST/GET /snts/{snt_id}/documents/accruals` + `/{doc_id}/post` + `/{doc_id}/unpost`
  - `POST/GET /snts/{snt_id}/documents/payments` + `/{doc_id}/post` + `/{doc_id}/unpost`
  - `GET /snts/{snt_id}/reports/balance?on_date=YYYY-MM-DD`
- Реализованы сервисы проведения/отмены (строго по алгоритму пересчёта движений):
  - `backend_snt_core/app/services/posting/accrual.py`
  - `backend_snt_core/app/services/posting/payment.py`.

### Тестовые данные (seed)

- Добавлен скрипт сидирования:
  - `backend_snt_core/scripts/seed.py`
  - создаёт 3 СНТ; в каждом 10–15 собственников и 10–15 участков;
  - создаёт статьи начислений; создаёт документы начисления/оплаты и проводит их (создаёт движения в регистре).

### Запуск и тестирование

- Добавлен скрипт запуска: `backend_snt_core/run.ps1` (миграции + seed + запуск API).
- Запущен FastAPI‑сервер на порту 8000 (в фоне).
- Открыт Swagger UI в браузере: `http://127.0.0.1:8000/docs`.

**Важно**: перед запуском необходимо:
  1) Убедиться, что PostgreSQL запущен и доступен по `DATABASE_URL` (по умолчанию `postgresql+psycopg://postgres:postgres@127.0.0.1:5432/snt_core`).
  2) Выполнить миграции: `.venv\Scripts\alembic -c backend_snt_core\alembic.ini upgrade head`.
  3) Выполнить seed: `.venv\Scripts\python -c "import sys; sys.path.insert(0, 'backend_snt_core'); from scripts.seed import main; main()"`.

