# Backend SNT v2

Физ. лица, члены СНТ, участки. API на FastAPI, БД SQLite.

## Запуск

```powershell
cd backend_snt_v2
python scripts/init_db.py   # миграции + seed (один раз)
python -m uvicorn app.main:app --app-dir . --reload --port 8001
```

Или `.\run.ps1` (если есть `.venv` в корне проекта).

API: `http://localhost:8001`. Документация: `http://localhost:8001/docs`.

Фронтенд ожидает API на `http://localhost:8001`. Запустите его отдельно (`frontend/run.ps1` или `run-frontend.ps1`).
