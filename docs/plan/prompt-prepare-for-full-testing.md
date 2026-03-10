# Промпт: Подготовка к полноценному тестированию проекта

**Назначение:** Использовать этот промпт в новой сессии для подготовки проекта к full testing и production-ready состоянию.

**Контекст:** Ledger-ready MVP (Этапы 1-5) завершён, merge в main выполнен. Осталось 15 непроходящих тестов, которые блокируют 100% готовность проекта.

---

## Промпт для агента (скопируй и вставь в начале сессии)

```
Ты — senior backend developer + QA engineer. Твоя задача: подготовить проект к полноценному тестированию и production-ready состоянию.

## Контекст

Ledger-ready MVP завершён (Этапы 1-5):
- ✅ Immutability amount реализована
- ✅ Domain events созданы и работают
- ✅ 7 новых тестов прошли
- ✅ ruff check passed
- ✅ Merge в main выполнен, отправлено в origin/main

**Проблема:** 15 существующих тестов не проходят (не связаны с Ledger-ready).

## Твоя миссия

Исправить 15 непроходящих тестов, чтобы проект был на 100% готов к production.

## Приоритеты (строго по порядку)

### Приоритет 1: MeterRepository и MeterReadingRepository (11 тестов)

**Файлы:**
- `backend/app/modules/meters/infrastructure/repositories.py`
- `backend/tests/test_api/test_meters.py`

**Проблема:** Репозитории не реализуют все методы интерфейса `IRepository`.

**Задача:**
1. Открой `backend/app/modules/meters/domain/repositories.py` → посмотри интерфейс `IMeterRepository`
2. Открой `backend/app/modules/meters/infrastructure/repositories.py` → найди класс `MeterRepository`
3. Добавь отсутствующие методы:
   - `async def get_all(self, cooperative_id: UUID) -> list[Meter]`
   - Для `MeterReadingRepository`: `get_by_id`, `get_all`, `update`, `delete`
4. Запусти тесты: `pytest tests/test_api/test_meters.py -v`
5. Убедись, что все 11 тестов прошли

**Подсказка:** Посмотри реализацию в `PaymentRepository` или `AccrualRepository` как образец.

### Приоритет 2: Land plots тесты (3 теста)

**Файлы:**
- `backend/tests/test_api/test_land_plots.py`

**Проблемы:**
1. `test_create_land_plot_with_multiple_owners` — IntegrityError (UNIQUE constraint failed)
2. `test_delete_land_plot_by_admin` — 404 вместо 204
3. `test_create_land_plot_auto_creates_financial_subject` — assertion None is not None

**Задача:**
1. Запусти тесты: `pytest tests/test_api/test_land_plots.py -v --tb=short`
2. Разберись с каждой ошибкой:
   - IntegrityError: проверь фикстуры, возможно дублируются ID
   - 404: проверь, создаётся ли land plot корректно
   - FinancialSubject: проверь, срабатывает ли event handler
3. Исправь ошибки
4. Запусти тесты снова, убедись, что все 3 прошли

### Приоритет 3: Reports тест (1 тест)

**Файл:**
- `backend/tests/test_api/test_reports.py`

**Проблема:**
- `test_get_debtors_report_invalid_cooperative_id` — ожидает 400, получает 422

**Задача:**
1. Открой тест, посмотри на assertion
2. Измени `assert response.status_code == 400` на `assert response.status_code == 422`
3. Запусти тест: `pytest tests/test_api/test_reports.py::test_get_debtors_report_invalid_cooperative_id -v`
4. Убедись, что тест прошёл

**Обоснование:** FastAPI автоматически валидирует UUID через Pydantic и возвращает 422 (Unprocessable Entity), а не 400.

## Проверки после каждого приоритета

После исправления каждого приоритета запускай:

```bash
# Запусти тесты этого модуля
pytest tests/test_api/test_{module}.py -v

# Запусти ruff check
ruff check .

# Убедись, что нет новых ошибок
```

## Финальная проверка (когда все 15 тестов исправлены)

```bash
# Запусти все тесты
pytest

# Ожидаемый результат: все 181 тест прошли
# Если есть неудачи — разберись и исправь

# Запусти ruff check
ruff check .

# Запусти architecture linter
python -m app.scripts.architecture_linter

# Запусти seed_db (проверка, что данные создаются)
python -m app.scripts.seed_db
```

## Документирование

Когда все тесты прошли:

1. **Обнови `docs/project-implementation.md`:**
   - Найди секцию "Тесты" (фичи 21-35)
   - Отметь, что все тесты проходят (181/181)

2. **Обнови `docs/development-index.md`:**
   - Секция "Топ-5": убери задачу "Исправить 15 тестов"
   - Добавь новую задачу из следующего приоритета

3. **Обнови `docs/plan/current-focus.md`:**
   - Напиши, что все 15 тестов исправлены
   - Проект готов к production на 100%

4. **Сделай коммит:**
   ```bash
   git add .
   git commit -m "fix: all 15 failing tests fixed - project 100% ready for production"
   git push origin main
   ```

## Критерии готовности

- ✅ Все 181 тест прошли
- ✅ ruff check: 0 ошибок
- ✅ architecture_linter: exit code 0
- ✅ seed_db: данные создаются без ошибок
- ✅ Документация обновлена

## Если что-то пошло не так

- **Тесты падают с другой ошибкой:** запиши ошибку, проанализируй, спроси у пользователя
- **Не можешь найти причину:** открой issue, запиши проблему, переходи к следующему тесту
- **Серьёзные архитектурные изменения:** остановись, спроси пользователя перед внесением

## Начни работу

1. Скажи мне, какую задачу берёшь (Приоритет 1, 2 или 3)
2. Назови ветку (если создаёшь новую — предложи имя)
3. Начни с Приоритета 1 (MeterRepository)
```

---

## Короткая версия (если нужно быстро начать)

```
Исправь 15 непроходящих тестов:
1. MeterRepository: добавить get_all(), update(), delete() (11 тестов)
2. Land plots: исправить IntegrityError и 404 (3 теста)
3. Reports: изменить 400 → 422 в тесте (1 тест)

После каждого исправления: pytest, ruff check.
Когда все прошли: обнови документацию, сделай коммит в main.
```

---

## Ожидаемый результат

После выполнения этой задачи:
- ✅ **100% тестов проходят** (181/181)
- ✅ **Проект готов к production**
- ✅ **Документация актуальна**
- ✅ **Технический долг минимизирован**

**Время на выполнение:** 2-4 часа (в зависимости от сложности отладки).

**Риски:** Низкие — все проблемы локализованы, решения понятны.

---

*Создан: 2026-03-10, после завершения Ledger-ready MVP (Этапы 1-5)*
