# Журнал изменений (v2: физ. лица, члены СНТ, участки)

Все изменения в рамках `PLAN_V2_IMPLEMENTATION.md` фиксируются здесь.  
Формат: дата (UTC), описание, затронутые файлы.

---

## 2026-01-24

- **План и журнал:** созданы `PLAN_V2_IMPLEMENTATION.md` и `CHANGELOG_IMPLEMENTATION.md`.

- **Backend v2:** добавлена папка `backend_snt_v2/`.
  - `requirements.txt`, `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/README`, `alembic/versions/0001_init_v2.py`
  - `app/config.py`, `app/db/base.py`, `app/db/session.py`
  - Модели: `app/models/physical_person.py`, `snt.py`, `snt_member.py`, `plot.py`, `plot_owner.py`, `__init__.py`
  - Схемы: `app/schemas/v2.py`
  - API: `app/api/router.py` — `GET /api/snts`, `GET /api/physical-persons`, `GET /api/physical-persons/{id}`, `GET /api/snt-members?snt_id=`, `GET /api/plots?snt_id=`
  - `app/main.py` (FastAPI + CORS), `scripts/seed.py`, `scripts/init_db.py`, `run.ps1`
  - SQLite `snt_v2.db`, тестовые данные: 3 СНТ, 8 физ. лиц, членства, участки, владельцы (Сидоров — два СНТ и два участка).

- **Frontend v2:** обновлены `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`.
  - Навигация: Обзор, СНТ, Физ. лица, Члены СНТ, Участки. Данные с `http://localhost:8001/api`.
  - Переключатель СНТ в шапке (из API); при смене СНТ — перезагрузка членов и участков.
  - Обзор: карточки (физ. лица, СНТ, члены и участки выбранного СНТ).
  - Физ. лица: таблица; клик по строке → модалка с деталями (телефон, ИНН, членства, участки).
  - Члены СНТ / Участки: таблицы, фильтр по выбранному СНТ.
  - Минималистичный UI (DM Sans, нейтральная палитра, простые иконки), переключатель темы сохранён.
  - Добавлены `run-v2.ps1` (запуск backend + frontend), `backend_snt_v2/README.md`.

---

## 2026-01-24 (счётчики, пользователи, изоляция)

- **Счётчики (meters):**
  - Модель `app/models/meter.py`: `snt_id`, `plot_id`, `meter_type` (electricity, water), `serial_number`. Уникальность `(snt_id, plot_id, meter_type)`.
  - Миграция `0002_meter_app_user`: таблицы `meter`, `app_user`.
  - Seed: у каждого участка по два счётчика (вода + электричество). Сидоров имеет несколько участков → несколько счётчиков.
  - API: `GET /api/meters?snt_id=`. Список счётчиков с типом и номером.

- **Пользователи и роли (авторизация без пароля):**
  - Модель `app/models/app_user.py`: `name`, `role` (admin | snt_user), `snt_id` (для snt_user).
  - Seed: пользователь «Администратор» (admin, snt_id=null); по одному пользователю с именем = название СНТ (snt_user, snt_id=этот СНТ).
  - API: `GET /api/users` (список для выбора пользователя), `GET /api/me` (текущий пользователь по заголовку `X-User-Id`).
  - Все запросы к защищённым эндпоинтам передают `X-User-Id`. Выбор пользователя — единственная «авторизация».

- **Строгая изоляция данных для snt_user:**
  - **Администратор:** видит все СНТ, переключатель СНТ в шапке, все данные.
  - **Пользователь-СНТ** (имя = СНТ): переключатель СНТ **скрыт**, доступ только к своему СНТ. Члены, участки, физ. лица, счётчики — только в рамках своего товарищества.
  - Реализация: зависимость `get_current_user` (заголовок `X-User-Id`), во всех эндпоинтах фильтрация по `user.snt_id` для `snt_user`. Нет возможности просмотра данных другого СНТ.

- **Frontend:**
  - Селектор пользователя в шапке; сохранение выбора в `localStorage`.
  - При выборе пользователя-СНТ переключатель СНТ скрыт, данные только по его СНТ.
  - Раздел «Счётчики»: таблица (участок, СНТ, тип, № счётчика). Загрузка `GET /api/meters` с `X-User-Id`.
  - Все вызовы API (кроме `/users`) отправляют `X-User-Id`.

- **Файлы:** `app/models/meter.py`, `app/models/app_user.py`, `alembic/versions/0002_meter_app_user.py`, `app/api/deps.py`, `app/api/router.py`, `app/schemas/v2.py`, `scripts/seed.py`, `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`.
