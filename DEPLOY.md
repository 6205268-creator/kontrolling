# Docker Деплой Controlling

## Быстрый старт

1. **Убедитесь, что Docker Desktop запущен**

2. **Запустите все сервисы:**
   ```bash
   docker compose up --build
   ```

   Или в фоновом режиме:
   ```bash
   docker compose up --build -d
   ```

3. **Проверьте статус контейнеров:**
   ```bash
   docker compose ps
   ```

4. **Остановите сервисы:**
   ```bash
   docker compose down
   ```

## Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| PostgreSQL | 5432 | База данных |
| Backend (FastAPI) | 8000 | API сервер |

Фронтенд в Docker **не запускается**. Для разработки фронтенд запускается локально: из корня `npm run dev`, приложение — http://localhost:5173.

## Доступ к приложениям

- **Frontend (приложение):** после `npm run dev` из корня — http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Документация (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

## Переменные окружения

Политика окружений (local dev, CI, production), источники переменных и работа с секретами описаны в [Environment Policy](docs/architecture/environment-policy.md).

### Backend
- `DATABASE_URL` — строка подключения к PostgreSQL (настраивается автоматически в docker-compose)
- `SECRET_KEY` — секретный ключ для JWT
- `ALGORITHM` — алгоритм шифрования (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` — время жизни токена

### Frontend
- Фронтенд для разработки запускается **локально**: из корня `npm run dev`, приложение — http://localhost:5173 (прокси `/api` на backend).
- Для production-сборки можно собрать образ из `frontend/Dockerfile` (Nginx + статика) отдельно.

## Полезные команды

```bash
# Просмотр логов
docker compose logs -f backend

# Перезапуск отдельного сервиса
docker compose restart backend

# Вход в контейнер
docker compose exec backend sh
docker compose exec db psql -U postgres -d controlling

# Очистка (удаление volumes с данными)
docker compose down -v
```

## Структура файлов

```
kontrolling/
├── docker-compose.yml       # Конфигурация всех сервисов
├── backend/
│   ├── Dockerfile           # Образ backend
│   └── .dockerignore        # Исключения для backend
└── frontend/
    ├── Dockerfile           # Образ frontend (multi-stage)
    ├── nginx.conf           # Конфигурация Nginx
    └── .dockerignore        # Исключения для frontend
```

## Примечания

- Данные PostgreSQL сохраняются в volume `postgres_data`
- Backend автоматически применяет миграции Alembic при запуске
- Фронтенд в разработке один: локальный Vite (`npm run dev`) на http://localhost:5173; в docker-compose фронтенд не входит
