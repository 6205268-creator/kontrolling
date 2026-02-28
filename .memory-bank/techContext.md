# Tech Context

## 🛠️ Технологический стек

### Backend

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Python** | 3.14 | Язык программирования |
| **FastAPI** | 0.115+ | Web framework |
| **SQLAlchemy** | 2.0+ | ORM |
| **Alembic** | latest | Миграции БД |
| **Pydantic** | 2.0+ | Валидация данных |
| **pytest** | 8.0+ | Тестирование |
| **pytest-asyncio** | latest | Async тесты |

**Зависимости** (`backend/pyproject.toml`):
```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.13.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "asyncpg>=0.29.0",
    "aiosqlite>=0.19.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
]
```

---

### Frontend

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Vue** | 3.4+ | Framework |
| **TypeScript** | 5.0+ | Язык |
| **Vite** | 5.0+ | Build tool |
| **Pinia** | 2.0+ | State management |
| **Vue Router** | 4.0+ | Routing |
| **Axios** | 1.0+ | HTTP client |

**Зависимости** (`frontend/package.json`):
```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "pinia": "^2.1.0",
    "vue-router": "^4.3.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0"
  }
}
```

---

### Infrastructure

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Docker** | latest | Контейнеризация |
| **Docker Compose** | latest | Оркестрация |
| **PostgreSQL** | 15+ | База данных |
| **Nginx** | latest | Reverse proxy (prod) |

---

## 🚀 Разработка

### Требования

- Python 3.14+
- Node.js 20+
- Docker Desktop (опционально)
- Git

### Установка (Backend)

```bash
cd backend

# Создать venv
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Установить зависимости
pip install -e .

# Запустить тесты
pytest

# Запустить сервер
python -m uvicorn app.main:app --reload
```

### Установка (Frontend)

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev server
npm run dev

# Собрать production
npm run build
```

### Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

---

## 📁 Структура проекта

```
kontrolling/
├── backend/
│   ├── app/
│   │   ├── modules/          # Clean Architecture модули
│   │   │   ├── shared/
│   │   │   ├── cooperative_core/
│   │   │   ├── land_management/
│   │   │   ├── financial_core/
│   │   │   ├── accruals/
│   │   │   ├── payments/
│   │   │   ├── expenses/
│   │   │   ├── meters/
│   │   │   ├── reporting/
│   │   │   └── administration/
│   │   ├── api/
│   │   ├── db/
│   │   ├── core/
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── router/
│   │   └── App.vue
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── docs/                     # Документация
├── tasks/                    # Управление задачами
├── domains/                  # Domain artifacts
├── .cursor/                  # Cursor IDE
├── .memory-bank/             # MCP Memory Bank
├── docker-compose.yml
└── README.md
```

---

## 🔧 Конфигурация

### Backend (`.env`)

```env
PROJECT_NAME=kontrolling
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/kontrolling
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (`.env`)

```env
VITE_API_URL=http://localhost:8000
VITE_PROJECT_NAME=kontrolling
```

---

## 🧪 Тестирование

### Backend

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app

# Конкретный файл
pytest tests/test_api/test_land_plots.py

# С выводом логов
pytest -s
```

### Frontend

```bash
# Unit тесты (планируется)
npm run test

# E2E тесты (планируется)
npm run test:e2e
```

---

## 📦 Деплой

### Docker Compose (Production)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db:5432/kontrolling
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
  
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### GitHub Actions (CI/CD)

**Планируется**:
- Тесты при каждом PR
- Docker build при merge в main
- Авто-деплой на staging

---

## 🔗 Полезные ссылки

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Vue 3**: https://vuejs.org/
- **Pinia**: https://pinia.vuejs.org/
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html

---

## 🆘 Troubleshooting

### Backend не запускается

```bash
# Проверить зависимости
pip install -e .

# Проверить БД
docker-compose up -d db

# Проверить переменные окружения
echo $DATABASE_URL
```

### Frontend не собирается

```bash
# Очистить кэш
rm -rf node_modules package-lock.json
npm install

# Проверить версию Node
node --version  # Должно быть 20+
```

### Тесты падают

```bash
# Запустить с отладкой
pytest -s --tb=long

# Проверить фикстуры
pytest --fixtures
```

---

*Последнее обновление: 28 февраля 2026*
