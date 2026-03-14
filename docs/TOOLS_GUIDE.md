# 🛡️ Инструменты качества кода — Руководство

**Дата:** 2026-03-12  
**Статус:** ✅ Все инструменты установлены и настроены

---

## 📦 Что установлено

### ✅ Pre-commit (backend + frontend)

**Автоматические проверки перед каждым коммитом:**

| Проверка | Где | Что делает |
|----------|-----|------------|
| **Ruff lint** | Backend | Проверка стиля Python |
| **Ruff format** | Backend | Форматирование кода |
| **Pytest** | Backend | Запуск всех тестов |
| **Architecture linter** | Backend | Проверка границ слоёв |
| **ESLint** | Frontend | Проверка TypeScript/Vue |
| **Type Coverage** | Frontend | Проверка покрытия типов (≥95%) |
| **Vitest** | Frontend | Запуск unit-тестов |

**Установка уже выполнена:**
```bash
pip install pre-commit
pre-commit install  # Уже выполнено
```

---

### ✅ Coverage для тестов

**Backend (pytest-cov):**
```bash
cd backend
pytest  # Автоматически показывает coverage
pytest --cov-report=html  # HTML отчёт в htmlcov/
```

**Frontend (Vitest coverage):**
```bash
cd frontend
npm run test:coverage  # Показывает % покрытия
```

**Требование:** Минимум 80% покрытия для backend (настраивается в `pyproject.toml`)

---

### ✅ Type Coverage (frontend)

**Проверка покрытия типов TypeScript:**
```bash
cd frontend
npm run type-coverage
```

**Требование:** ≥95% кода с типами

**Что проверяет:**
- Отсутствие `any` без необходимости
- Явные типы для props, emits, refs
- Полные типы для функций

---

### ✅ GitGuardian (защита секретов)

**Назначение:** Не даёт закоммитить секреты (API keys, passwords, токены)

**GitHub Actions:**
- Автоматическая проверка при push и PR
- Блокировка коммитов с секретами

**Локальная проверка:**
```bash
# Установка (опционально)
pip install ggshield

# Сканирование
ggshield secret scan .
```

**Настройка:** `.gitguardian.example.yaml` (скопируй в `.gitguardian.yaml`)

**Важно:** Для работы GitHub Actions нужно добавить `GITGUARDIAN_API_KEY` в Secrets репозитория.

---

### ✅ Dependency Check (уязвимости зависимостей)

**Backend:**
```bash
cd backend

# Проверка уязвимостей
pip-audit

# Проверка обновлений
pip-review --interactive

# Обновление всех зависимостей
pip-review --auto
```

**Frontend:**
```bash
cd frontend

# Проверка уязвимостей
npm audit

# Автоматическое исправление
npm audit fix

# Обновление зависимостей
npm install -g npm-check-updates
ncu -i  # Интерактивное обновление
```

**Рекомендация:** Запускать раз в неделю

---

## 🚀 Быстрый старт

### Перед первым коммитом

**Backend:**
```bash
cd backend
pip install -e ".[dev]"  # Установить dev зависимости
```

**Frontend:**
```bash
cd frontend
npm install  # Установить зависимости
```

### Запуск всех проверок вручную

**Backend:**
```bash
cd backend
ruff check . && ruff format --check . && pytest --cov=app
```

**Frontend:**
```bash
cd frontend
npm run lint && npm run type-coverage && npm run test:coverage
```

---

## 📊 Типичные проблемы и решения

### Pre-commit не проходит

**Ошибка:** Ruff lint
```bash
# Автоматическое исправление
ruff check . --fix
ruff format .
```

**Ошибка:** Pytest
```bash
# Запустить тесты и увидеть, какие упали
pytest -v
```

**Ошибка:** Architecture linter
```bash
# Проверить, какие нарушения
python -m app.scripts.architecture_linter
```

### Type Coverage < 95%

**Проблема:** Используется `any`
```typescript
// ❌ Плохо
const data: any = fetchData()

// ✅ Хорошо
interface DataType { ... }
const data: DataType = fetchData()
```

**Проблема:** Неявные типы
```typescript
// ❌ Плохо
const users = ref([])

// ✅ Хорошо
interface User { id: string; name: string }
const users = ref<User[]>([])
```

### Тесты не проходят

**Backend:**
```bash
# Запустить один тест
pytest tests/test_file.py::test_function -v

# Запустить с выводом логов
pytest -s
```

**Frontend:**
```bash
# Запустить один тест
npm run test -- testFile.spec.ts

# Запустить с UI
npm run test:coverage -- --ui
```

---

## 🔧 Настройка

### Backend (pyproject.toml)

```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"
# Изменить минимальное покрытие: --cov-fail-under=XX
```

### Frontend (package.json)

```json
"scripts": {
  "type-coverage": "type-coverage --at-least 95 --strict"
  # Изменить минимальное покрытие: --at-least=XX
}
```

### Pre-commit (.pre-commit-config.yaml)

Добавить новые проверки:
```yaml
- repo: local
  hooks:
    - id: custom-check
      name: Custom Check
      entry: python scripts/custom_check.py
      language: system
      files: ^backend/
```

---

## 📈 Мониторинг качества

### Еженедельный чек-лист

- [ ] `pip-audit` — нет уязвимостей
- [ ] `npm audit` — нет уязвимостей
- [ ] `pytest --cov` — покрытие ≥80%
- [ ] `npm run type-coverage` — покрытие ≥95%
- [ ] Pre-commit проходит без ошибок

### Интеграция с CI/CD

**GitHub Actions уже настроены:**
- Backend tests (pytest + ruff)
- Architecture linter
- GitGuardian scan (нужно добавить API key)

**Добавить проверку coverage:**
```yaml
- name: Test with coverage
  run: |
    cd backend
    pytest --cov=app --cov-fail-under=80
```

---

## 📚 Дополнительные ресурсы

- [Pre-commit документация](https://pre-commit.com/)
- [Ruff документация](https://docs.astral.sh/ruff/)
- [Pytest-cov документация](https://pytest-cov.readthedocs.io/)
- [Type Coverage документация](https://github.com/plantain-00/type-coverage)
- [GitGuardian документация](https://docs.gitguardian.com/)
- [Vitest Coverage](https://vitest.dev/guide/coverage.html)

---

*Обновляй этот документ при добавлении новых инструментов*
