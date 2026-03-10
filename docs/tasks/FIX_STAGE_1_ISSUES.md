# Исправление проблем Этапа 1 (Ledger-ready MVP)

**Назначение:** Инструкция для модели-разработчика по исправлению проблем, обнаруженных при проверке Этапа 1.

**Контекст:** Этап 1 выполнен верно (миграция, модели, домен, DTO, API, тесты), но при проверке обнаружены 3 проблемы, не связанные напрямую с Этапом 1, но требующие исправления.

---

## Список проблем

| # | Проблема | Приоритет | Файлы |
|---|----------|-----------|-------|
| 1 | `ExpenseRepository` не реализует `get_all` | **Критично** (блокирует тесты) | `backend/app/modules/expenses/infrastructure/repositories.py` |
| 2 | Ruff: 112 ошибок стиля (импорты, unused variables) | Средний | Множество файлов |
| 3 | Seed: Unicode ошибка при выводе эмодзи | Низкий | `backend/app/scripts/seed_db.py` |

---

## Проблема 1: ExpenseRepository не реализует `get_all`

### Симптом

```
TypeError: Can't instantiate abstract class ExpenseRepository without an implementation for abstract method 'get_all'
```

**Где:** Все тесты `tests/test_api/test_expenses.py` (11 тестов)

### Причина

В `backend/app/modules/expenses/domain/repositories.py` интерфейс `IExpenseRepository` требует метод `get_all`, но в реализации `backend/app/modules/expenses/infrastructure/repositories.py` этот метод отсутствует.

### Решение

**Файл:** `backend/app/modules/expenses/infrastructure/repositories.py`

**Добавить метод в класс `ExpenseRepository`:**

```python
async def get_all(self, cooperative_id: UUID) -> list[Expense]:
    """Get all expenses for a cooperative (alias for get_by_cooperative)."""
    return await self.get_by_cooperative(cooperative_id)
```

**ИЛИ** (если метод должен быть в интерфейсе):

Проверить интерфейс в `backend/app/modules/expenses/domain/repositories.py`:

```python
class IExpenseRepository(ABC):
    """Interface for Expense repository."""

    @abstractmethod
    async def get_by_id(self, id: UUID, cooperative_id: UUID) -> Expense | None:
        """Get expense by ID."""
        pass

    @abstractmethod
    async def get_by_cooperative(self, cooperative_id: UUID) -> list[Expense]:
        """Get all expenses for a cooperative."""
        pass

    @abstractmethod
    async def add(self, entity: Expense) -> Expense:
        """Add new expense."""
        pass

    @abstractmethod
    async def update(self, entity: Expense) -> Expense:
        """Update existing expense."""
        pass

    @abstractmethod
    async def delete(self, id: UUID, cooperative_id: UUID) -> None:
        """Delete expense by ID."""
        pass

    # УБРАТЬ этот метод если он не нужен:
    # @abstractmethod
    # async def get_all(self, cooperative_id: UUID) -> list[Expense]:
    #     pass
```

**Проверка:**

```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_api/test_expenses.py -v
```

**Ожидаемый результат:** Все 11 тестов проходят.

---

## Проблема 2: Ruff — 112 ошибок стиля

### Симптом

```
Found 112 errors.
[*] 76 fixable with the `--fix` option
```

### Типы ошибок

| Код | Описание | Кол-во | Как исправить |
|-----|----------|--------|---------------|
| `I001` | Import block is un-sorted | ~60 | `ruff check . --fix` |
| `F401` | Imported but unused | ~10 | Удалить неиспользуемые импорты |
| `F841` | Local variable assigned but never used | ~10 | Удалить присваивание или использовать |
| `F821` | Undefined name (forward reference) | ~10 | Это норма для SQLAlchemy, игнорировать |
| `E402` | Module level import not at top | ~2 | Переместить импорты вверх |

### Решение

**Шаг 1: Автоматическое исправление сортировки импортов**

```bash
cd backend
.\venv\Scripts\python.exe -m ruff check . --fix
```

**Шаг 2: Проверить оставшиеся ошибки**

```bash
.\venv\Scripts\python.exe -m ruff check .
```

**Шаг 3: Исправить F401 (unused imports) вручную**

Примеры файлов с F401:

1. **`app/modules/accruals/api/routes.py`** — удалить `get_get_accrual_use_case`
2. **`app/modules/payments/api/routes.py`** — удалить `get_get_payment_use_case`
3. **`app/modules/accruals/application/use_cases.py`** — удалить `AccrualUpdate` если не используется

**Шаг 4: Исправить F841 (unused variables) вручную**

Примеры:

1. **`tests/test_api/test_expenses.py:176`** — удалить `response =` или использовать
2. **`tests/test_api/test_expenses.py:205`** — удалить `response =` или использовать
3. **`tests/test_api/test_financial_subjects.py:89`** — удалить `accrual =` или использовать
4. **`tests/test_api/test_financial_subjects.py:102`** — удалить `payment =` или использовать
5. **`tests/test_models/test_accrual.py:114`** — удалить `accrual =` или использовать
6. **`tests/test_models/test_expense.py:101`** — удалить `expense =` или использовать
7. **`tests/test_models/test_payment.py:106`** — удалить `payment =` или использовать

**Шаг 5: Игнорировать F821 (forward references)**

Это SQLAlchemy pattern с строковыми типами:

```python
def to_domain(self) -> "Payment":  # Это нормально
    from app.modules.payments.domain.entities import Payment
    ...
```

**Проверка:**

```bash
cd backend
.\venv\Scripts\python.exe -m ruff check .
```

**Ожидаемый результат:** 0 ошибок (или только F821 которые игнорируются).

---

## Проблема 3: Seed — Unicode ошибка при выводе эмодзи

### Симптом

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-1: character maps to <undefined>
```

### Причина

Windows использует кодировку cp1251 для консоли, которая не поддерживает эмодзи (ℹ️, ✅, ❌).

### Решение

**Файл:** `backend/app/scripts/seed_db.py`

**Вариант 1: Заменить эмодзи на ASCII-символы**

```python
# Было:
print("ℹ️ СТ уже существуют, пропускаем создание")
print("✅ Создано 2 СТ")

# Стало:
print("[INFO] СТ уже существуют, пропускаем создание")
print("[OK] Создано 2 СТ")
```

**Вариант 2: Установить UTF-8 кодировку для вывода**

В начало файла `seed_db.py` (после импортов):

```python
import sys
import io

# Установить UTF-8 для stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

**Вариант 3: Использовать `print` с `encoding='utf-8'`**

Заменить все `print()` на:

```python
import sys

def safe_print(text: str) -> None:
    """Print with UTF-8 encoding."""
    print(text.encode('utf-8', errors='replace').decode('utf-8'))

# Использовать:
safe_print("✅ Создано 2 СТ")
```

**Рекомендация:** Использовать Вариант 1 (ASCII-символы) — проще и надёжнее.

**Проверка:**

```bash
cd backend
.\venv\Scripts\python.exe -m app.scripts.seed_db
```

**Ожидаемый результат:** Скрипт выполняется без ошибок, создаёт тестовые данные.

---

## Чек-лист выполнения

### После исправления всех проблем:

```bash
cd backend

# 1. Тесты expenses
.\venv\Scripts\python.exe -m pytest tests/test_api/test_expenses.py -v

# 2. Все API тесты
.\venv\Scripts\python.exe -m pytest tests/test_api/ -v

# 3. Все модельные тесты
.\venv\Scripts\python.exe -m pytest tests/test_models/ -v

# 4. Ruff
.\venv\Scripts\python.exe -m ruff check .

# 5. Architecture linter
.\venv\Scripts\python.exe -m app.scripts.architecture_linter

# 6. Seed
.\venv\Scripts\python.exe -m app.scripts.seed_db
```

**Ожидаемый результат:**

- ✅ Все тесты проходят (31 API + 13 моделей)
- ✅ Ruff: 0 ошибок
- ✅ Architecture linter: All checks passed
- ✅ Seed: выполняется без ошибок

---

## Ссылки

- **Спецификация Этапа 1:** `docs/tasks/IMPLEMENTATION_SPEC_LEDGER_READY.md`
- **Результаты проверки:** `docs/tasks/FIX_STAGE_1_ISSUES.md` (этот файл)
- **Workflow:** `docs/tasks/workflow-orchestration.md`

---

*Создано: 2026-03-09*
*Для: Модель-разработчик для исправления проблем Этапа 1*
