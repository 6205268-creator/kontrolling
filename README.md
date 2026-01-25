# Ядро учёта хозяйственной деятельности СНТ

Проект реализует **1С‑подобную пересчитываемую модель** учёта для СНТ:

- **PostgreSQL** — источник истины и контроль целостности (FK/CHECK/транзакции).
- **FastAPI + SQLAlchemy** — thin‑layer backend и сервисы проведения документов.
- UI/фронтенд не требуется для работы системы.

Архитектурное описание: `ARCHITECTURE_SNT_CORE.md` (формат Markdown, подходит для Obsidian).

## Быстрый старт (backend)

### 1) Настроить переменные окружения

Создайте файл `backend_snt_core/.env` (или задайте переменные окружения) и укажите:

- `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`

### 2) Установить зависимости (в venv)

В корне проекта:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r backend_snt_core\requirements.txt
```

### 3) Запустить backend

```powershell
.venv\Scripts\uvicorn app.main:app --app-dir backend_snt_core --reload --port 8000
```

После запуска откройте:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
