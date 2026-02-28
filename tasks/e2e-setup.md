# Фича 35: Финальная интеграция и E2E тесты

## Обзор

E2E тесты покрывают основные пользовательские сценарии:
1. Логин → Создание участка → Создание начисления → Регистрация платежа → Проверка баланса
2. Логин → Просмотр отчёта по должникам → Проверка корректности данных
3. Навигация по всем разделам
4. Создание владельца

## Предварительные требования

### 1. Backend должен быть запущен

```bash
cd backend
# Установите зависимости если не установлены
pip install -r requirements.txt

# Запустите с seed данными
python -m app.scripts.seed_db

# Запустите сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend должен быть запущен

```bash
cd frontend
npm install
npm run dev
```

### 3. Playwright установлен

```bash
cd frontend
npm install -D @playwright/test
npx playwright install chromium
```

## Запуск тестов

### Базовый запуск

```bash
cd frontend
npm run test:e2e
```

### Запуск с UI

```bash
npm run test:e2e:ui
```

### Запуск в браузере (headed)

```bash
npm run test:e2e:headed
```

### Запуск конкретного теста

```bash
npm run test:e2e -- --grep "full flow"
```

### Запуск с отчётом

```bash
npm run test:e2e -- --reporter=html
npx playwright show-report
```

## Структура тестов

```
frontend/e2e/
├── conftest.py           # Фикстуры для тестов
├── tests/
│   └── test_full_flow.spec.ts  # Основные E2E тесты
├── playwright.config.ts  # Конфигурация Playwright
└── README.md             # Документация
```

## Тестовые сценарии

### Сценарий 1: Полный финансовый цикл

```typescript
Логин (testuser / testpassword123)
  ↓
Создание участка (номер, площадь, кадастр)
  ↓
Создание начисления (сумма, описание)
  ↓
Регистраация платежа (сумма, документ)
  ↓
Проверка отчёта по должникам
```

### Сценарий 2: Навигация и авторизация

- Редирект на /login при отсутствии аутентификации
- Успешный logout
- Навигация по всем 7 разделам

### Сценарий 3: Создание сущностей

- Создание владельца
- Просмотр счётчиков
- Просмотр расходов

## Отладка тестов

### Режим отладки

```bash
npm run test:e2e -- --debug
```

### Pause в тесте

Добавьте в код теста:
```typescript
await page.pause();
```

### Трейсинг

```bash
npm run test:e2e -- --trace on
npx playwright show-trace
```

## Устранение проблем

### Тесты не находят элементы

Проверьте что:
1. Frontend запущен на http://localhost:5173
2. Backend запущен на http://localhost:8000
3. Данные seed загружены в БД

### Ошибки аутентификации

Убедитесь что пользователь существует в БД:
```bash
cd backend
python -m app.scripts.seed_db
```

### Проблемы с браузером

Переустановите браузеры:
```bash
npx playwright install --force
```

## Интеграция с CI/CD

Для GitHub Actions добавьте шаг:

```yaml
- name: Install Playwright
  run: |
    cd frontend
    npm install
    npx playwright install --with-deps chromium

- name: Run E2E tests
  run: |
    cd frontend
    npm run test:e2e
```
