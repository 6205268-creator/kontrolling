# 🛠️ Рекомендации по улучшению качества кода и разработки

**Дата:** 2026-03-12  
**Статус:** ✅ 5/5 инструментов приоритета 1 установлены

---

## ✅ Выполнено (2026-03-12)

| Инструмент | Статус | Описание |
|------------|--------|----------|
| **Pre-commit хуки** | ✅ Установлено | Ruff, Pytest, ESLint, Architecture linter |
| **Coverage тестов** | ✅ Установлено | pytest-cov (backend) + Vitest coverage (frontend) |
| **Type Coverage** | ✅ Установлено | Проверка ≥95% покрытия типами TypeScript |
| **Husky (frontend)** | ✅ Установлено | Pre-commit проверки для frontend |
| **GitGuardian** | ✅ Настроено | GitHub Actions workflow для защиты секретов |
| **Dependency Check** | ✅ Установлено | pip-audit + pip-review (backend), npm audit (frontend) |

**Документация:** [`docs/TOOLS_GUIDE.md`](TOOLS_GUIDE.md) — полное руководство по использованию.

---

## 📊 Текущий стек

### Backend (Python 3.11+)
| Инструмент | Версия | Назначение |
|------------|--------|------------|
| **FastAPI** | 0.129.0 | Веб-фреймворк |
| **SQLAlchemy** | 2.0.36+ | ORM (async) |
| **Pydantic** | 2.9.0 | Валидация данных |
| **Alembic** | 1.13.0+ | Миграции БД |
| **pytest** | 8.3.0+ | Тестирование |
| **ruff** | 0.5.0+ | Линтер + форматтер |
| **httpx** | 0.27.0+ | HTTP-клиент для тестов |

### Frontend (Vue 3)
| Инструмент | Версия | Назначение |
|------------|--------|------------|
| **Vue 3** | 3.5.25 | Фреймворк |
| **TypeScript** | 5.9.3 | Типизация |
| **Vite** | 7.3.1 | Сборка |
| **Pinia** | 3.0.4 | State management |
| **Vitest** | 2.1.6 | Unit-тесты |
| **Playwright** | 1.58.2 | E2E тесты |
| **ESLint** | 9.17.0 | Линтер |
| **Prettier** | 3.4.2 | Форматтер |

### MCP Серверы (уже подключены)
| Сервер | Статус | Назначение |
|--------|--------|------------|
| **Context7** | ✅ Подключен | Документация библиотек |
| **Memory Bank** | ✅ Подключен | Долговременная память |
| **Shadcn UI** | ✅ Подключен | UI компоненты |

---

## 🎯 Рекомендации по улучшению (приоритеты)

### 🔥 Приоритет 1: Критически важные (добавить сейчас)

#### 1.1 **Pre-commit хуки** ⭐⭐⭐
**Зачем:** Автоматическая проверка перед коммитом (lint, format, тесты)

**Установка:**
```bash
cd backend
pip install pre-commit
```

**Создать `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

**Активация:**
```bash
pre-commit install
```

**Результат:** Каждый коммит автоматически проверяется

---

#### 1.2 **Type Coverage для TypeScript** ⭐⭐⭐
**Зачем:** Контроль покрытия типов TypeScript (чтобы не было `any`)

**Установка:**
```bash
cd frontend
npm install -D type-coverage
```

**Добавить в `package.json`:**
```json
"scripts": {
  "type-coverage": "type-coverage --at-least 95"
}
```

**Запуск:**
```bash
npm run type-coverage
```

**Результат:** Минимум 95% кода с типами

---

#### 1.3 **Husky для pre-commit проверок на фронтенде** ⭐⭐⭐
**Зачем:** Автоматический lint + test перед коммитом

**Установка:**
```bash
cd frontend
npm install -D husky
npx husky init
```

**Добавить в `.husky/pre-commit`:**
```bash
npm run lint
npm run test
```

---

### 🚀 Приоритет 2: Важные для качества (добавить в спринт)

#### 2.1 **SonarQube / SonarCloud** ⭐⭐
**Зачем:** Статический анализ, поиск багов, code smells, дублирования

**Вариант 1: SonarCloud (бесплатно для open source)**
```yaml
# .github/workflows/sonarcloud.yml
name: SonarCloud Analysis
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  sonarcloud:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

**Вариант 2: SonarQube (self-hosted)**
```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:lts-community
```

---

#### 2.2 **Coverage для тестов** ⭐⭐
**Зачем:** Контроль покрытия тестами

**Backend (pytest-cov):**
```bash
cd backend
pip install pytest-cov
```

**Запуск:**
```bash
pytest --cov=app --cov-report=html --cov-fail-under=80
```

**Frontend (Vitest coverage):**
```bash
cd frontend
npm install -D @vitest/coverage-v8
```

**Запуск:**
```bash
npm run test -- --coverage --coverage.thresholds.100
```

---

#### 2.3 **Dependency Check** ⭐⭐
**Зачем:** Проверка устаревших и уязвимых зависимостей

**Backend (pip-audit + pip-review):**
```bash
pip install pip-audit pip-review
pip-audit  # Проверка уязвимостей
pip-review --interactive  # Обновление зависимостей
```

**Frontend (npm audit + npm-check-updates):**
```bash
npm audit  # Уязвимости
npm install -g npm-check-updates
ncu -i  # Обновление зависимостей
```

---

### 📚 Приоритет 3: MCP серверы для улучшения разработки

#### 3.1 **GitHub MCP Server** ⭐⭐⭐
**Зачем:** Работа с репозиторием без выхода из IDE

**Возможности:**
- Чтение файлов репозитория
- Поиск по коду
- Управление ветками
- Создание PR

**Установка:** Добавить в `.cursor/mcp.json`:
```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"]
}
```

---

#### 3.2 **PostgreSQL MCP Server** ⭐⭐
**Зачем:** Прямой доступ к БД для агента (просмотр схем, запросы)

**Установка:**
```json
"postgresql": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgresql"],
  "env": {
    "DATABASE_URL": "postgresql://user:password@localhost:5432/kontrolling"
  }
}
```

**Возможности:**
- Просмотр структуры таблиц
- Выполнение SELECT запросов
- Анализ данных

---

#### 3.3 **Playwright MCP Server** ⭐⭐
**Зачем:** Запуск E2E тестов агентом

**Установка:**
```json
"playwright": {
  "command": "npx",
  "args": ["-y", "@playwright/mcp-server"]
}
```

---

#### 3.4 **GitLab / Jira MCP** ⭐ (опционально)
**Зачем:** Интеграция с трекером задач

**Для Jira:**
```json
"jira": {
  "url": "https://your-domain.atlassian.net",
  "email": "your-email",
  "token": "your-api-token"
}
```

---

### 🎨 Приоритет 4: Улучшение frontend

#### 4.1 **Vue ESLint Plugin с правилами** ⭐⭐
**Уже есть:** `eslint-plugin-vue`

**Добавить строгие правила:**
```js
// eslint.config.js
export default [
  {
    plugins: {
      vue: require('eslint-plugin-vue'),
    },
    rules: {
      'vue/multi-word-component-names': 'error',
      'vue/require-explicit-emits': 'error',
      'vue/require-props': 'error',
      'vue/no-mutating-props': 'error',
    },
  },
]
```

---

#### 4.2 **Vue Test Utils для компонентных тестов** ⭐⭐
**Зачем:** Тестирование Vue компонентов

**Установка:**
```bash
npm install -D @vue/test-utils
```

**Пример теста:**
```typescript
import { mount } from '@vue/test-utils'
import MyComponent from './MyComponent.vue'

describe('MyComponent', () => {
  it('renders props', () => {
    const wrapper = mount(MyComponent, {
      props: { title: 'Test' }
    })
    expect(wrapper.text()).toContain('Test')
  })
})
```

---

#### 4.3 **Storybook для документации компонентов** ⭐
**Зачем:** Визуальная документация UI компонентов

**Установка:**
```bash
cd frontend
npx storybook@latest init
```

---

### 🔒 Приоритет 5: Безопасность

#### 5.1 **Secrets Detection** ⭐⭐⭐
**Зачем:** Не коммитить секреты (API keys, passwords)

**Вариант 1: GitGuardian (бесплатно для private repos)**
```bash
# .github/workflows/gitguardian.yml
name: GitGuardian Scan
on: [push, pull_request]
jobs:
  scanning:
    runs-on: ubuntu-latest
    steps:
      - name: GitGuardian Scan
        uses: GitGuardian/ggshield-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITGUARDIAN_API_KEY: ${{ secrets.GITGUARDIAN_API_KEY }}
```

**Вариант 2: detect-secrets (Yelp)**
```bash
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

---

#### 5.2 **Security Headers для API** ⭐⭐
**Добавить в `backend/app/main.py`:**
```python
from fastapi.middleware.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

---

#### 5.3 **Rate Limiting** ⭐⭐
**Зачем:** Защита от DDoS и brute force

**Установка:**
```bash
cd backend
pip install slowapi
```

**Настройка:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

---

## 📈 Итоговая таблица приоритетов

| Инструмент | Приоритет | Время на внедрение | Эффект |
|------------|-----------|-------------------|--------|
| **Pre-commit хуки** | 🔥 Критично | 30 мин | ⭐⭐⭐ |
| **Type Coverage** | 🔥 Критично | 15 мин | ⭐⭐⭐ |
| **Husky (frontend)** | 🔥 Критично | 20 мин | ⭐⭐⭐ |
| **GitHub MCP** | 🚀 Важно | 10 мин | ⭐⭐⭐ |
| **Coverage тестов** | 🚀 Важно | 30 мин | ⭐⭐ |
| **SonarCloud** | 🚀 Важно | 1 час | ⭐⭐ |
| **Playwright MCP** | 📚 MCP | 10 мин | ⭐⭐ |
| **PostgreSQL MCP** | 📚 MCP | 15 мин | ⭐⭐ |
| **Vue Test Utils** | 🎨 Frontend | 30 мин | ⭐⭐ |
| **GitGuardian** | 🔒 Security | 30 мин | ⭐⭐⭐ |
| **Rate Limiting** | 🔒 Security | 30 мин | ⭐⭐ |
| **Storybook** | 🎨 Frontend | 2 часа | ⭐ |

---

## 🎯 План действий (по шагам)

### Неделя 1: Критичное
- [ ] Pre-commit хуки (backend)
- [ ] Husky (frontend)
- [ ] Type Coverage
- [ ] GitHub MCP Server

### Неделя 2: Качество
- [ ] Coverage для тестов
- [ ] SonarCloud
- [ ] Dependency Check

### Неделя 3: MCP серверы
- [ ] PostgreSQL MCP
- [ ] Playwright MCP
- [ ] GitLab/Jira (если нужно)

### Неделя 4: Безопасность
- [ ] GitGuardian
- [ ] Rate Limiting
- [ ] Security Headers

---

## 📚 Полезные ссылки

- [MCP Market](https://mcpmarket.com/) — каталог MCP серверов
- [Context7 Documentation](https://context7.com/docs) — документация библиотек
- [Pre-commit Framework](https://pre-commit.com/) — хуки для git
- [SonarCloud](https://sonarcloud.io/) — бесплатный анализ кода
- [GitGuardian](https://www.gitguardian.com/) — защита секретов

---

*Обновляй этот документ при добавлении новых инструментов*
