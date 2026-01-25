# kontrolling — учёт хозяйственной деятельности СНТ

Проект реализует **1С‑подобную пересчитываемую модель** учёта для СНТ:

- **PostgreSQL** (v1) — документы, проводки, реестр остатков.
- **SQLite** (v2) — справочники: физлица, члены СНТ, участки, счётчики, пользователи. API :8001.
- **Frontend** (Vanilla JS) — дашборд, таблицы, модалки. Порт :3000.
- UI/фронтенд не является источником истины; все инварианты — в backend/БД.

Архитектура: `.ai/architecture.md`, `.ai/context.md`, `ARCHITECTURE_SNT_CORE.md`, `ARCHITECTURE_SNT_V2_PHYSICAL_PERSON.md`.

## Быстрый старт

### v2 + frontend (рекомендуется)

```powershell
.\run-v2.ps1
```

Инициализирует SQLite, запускает API :8001 и фронтенд :3000, открывает браузер.

### v1 (backend core, PostgreSQL)

1. Создайте `backend_snt_core/.env` с `DATABASE_URL=postgresql+psycag://...`
2. Миграции и seed — см. `backend_snt_core/README.md`, `DEV_LOG.md`
3. `.\backend_snt_core\run.ps1` — API :8000

### Зависимости

```powershell
python -m venv .venv
.venv\Scripts\pip install -r backend_snt_core\requirements.txt
.venv\Scripts\pip install -r backend_snt_v2\requirements.txt
```
