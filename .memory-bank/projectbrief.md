# Project Brief: КОНТРОЛЛИНГ

## 📋 Описание проекта

**Название**: КОНТРОЛЛИНГ — Система учёта хозяйственной деятельности садоводческих товариществ (СТ)

**Тип**: Веб-приложение (Full-stack)

**Миссия**: Автоматизация финансовых и операционных процессов садоводческих товариществ для повышения прозрачности и эффективности управления.

---

## 🎯 Основные возможности

### Для пользователей (владельцев участков)

- **Управление участками** — кадастровый учёт с правами собственности (долевое владение)
- **Финансы** — отслеживание баланса, начислений и платежей
- **Счётчики** — передача показаний приборов учёта (вода, электричество)
- **Отчёты** — анализ должников и движение денежных средств

### Для администрации СТ

- **Казначей** — полный доступ к финансовым операциям (начисления, платежи, расходы)
- **Председатель** — просмотр данных СТ, создание начислений
- **Администратор** — полный доступ ко всем функциям и данным всех СТ

---

## 🏗️ Архитектура

### Backend

- **Фреймворк**: FastAPI (Python 3.14)
- **База данных**: PostgreSQL + SQLAlchemy (async)
- **Миграции**: Alembic
- **Аутентификация**: JWT токены
- **Архитектура**: Clean Architecture (модульная)

**Модули**:
- `cooperative_core` — управление СТ
- `land_management` — участки и владельцы
- `financial_core` — финансовые субъекты и балансы
- `accruals` — начисления
- `payments` — платежи
- `expenses` — расходы
- `meters` — счётчики и показания
- `reporting` — отчёты
- `administration` — auth и пользователи

### Frontend

- **Фреймворк**: Vue 3 + Vite
- **Язык**: TypeScript
- **State Management**: Pinia
- **UI**: Bootstrap CSS + Material Design principles

### Инфраструктура

- **Docker**: Контейнеризация backend и frontend
- **Docker Compose**: Оркестрация сервисов

---

## 📁 Структура репозитория

```
kontrolling/
├── backend/
│   ├── app/
│   │   ├── modules/          # Clean Architecture модули
│   │   ├── api/              # API endpoints
│   │   ├── db/               # Database config
│   │   ├── core/             # Security, config
│   │   └── scripts/          # DB seed scripts
│   ├── tests/
│   └── alembic/              # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/       # Vue components
│   │   ├── views/            # Page views
│   │   ├── stores/           # Pinia stores
│   │   └── router/           # Vue Router
│   └── public/
├── docs/                     # Документация
├── tasks/                    # Управление задачами
├── domains/                  # Domain-driven design артефакты
└── .cursor/                  # Cursor IDE настройки
```

---

## 🔗 Ссылки на документацию

- **Основной дизайн**: [`docs/project-design.md`](docs/project-design.md)
- **Архитектура**: [`docs/architecture/`](docs/architecture/)
- **Модель данных**: [`docs/data-model/`](docs/data-model/)
- **Процессы (BPMN)**: [`docs/processes/`](docs/processes/)
- **Workflow**: [`tasks/workflow-orchestration.md`](tasks/workflow-orchestration.md)

---

## 👥 Ролевая модель

| Роль | Права |
|------|-------|
| **admin** | Полный доступ ко всем СТ |
| **chairman** | Просмотр данных своего СТ, создание начислений |
| **treasurer** | Полный доступ к финансовым операциям своего СТ |

---

## 🚀 Быстрый старт

```bash
# Клонирование
git clone https://github.com/6205268-creator/kontrolling.git
cd kontrolling

# Запуск через Docker
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## 📊 Статус проекта

**Текущая фаза**: Активная разработка

**Архитектура**: Clean Architecture (100% миграция завершена)

**Тесты**: 192 passed, 5 skipped

---

*Последнее обновление: 28 февраля 2026*
