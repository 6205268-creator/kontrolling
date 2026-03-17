# TASK: Исправление проблем по результатам аудита (2026-03-17)

**Статус:** 🟡 В работе (Части 1, 2 и 3 выполнены)  
**Ветка:** `feature/audit-fixes-20260317` (создана от `feature/2026-03-15-session`)  
**Приоритет:** Высокий  
**Создано:** 2026-03-17 (аудит текущей сессии)

---

## Контекст

Проведён полный аудит проекта. Обнаружены критичные баги, архитектурные нарушения и мелкий мусор. Ниже — согласованный с владельцем проекта план исправлений.

**Решения владельца по каждому пункту зафиксированы — менять приоритеты или объём без его одобрения нельзя.**

---

## Часть 1: КРИТИЧНЫЕ ИСПРАВЛЕНИЯ

### 1.1 Счётчики: неправильная работа с базой данных

**Файл:** `backend/app/modules/meters/api/routes.py` (эндпоинт GET `/api/meters/`)

**Проблема:**
- Код использует `anext(get_db())` — создаёт отдельную сессию БД вместо request-scoped.
- API-слой импортирует `MeterRepository` из infrastructure напрямую (нарушение Clean Architecture).

**Что сделать:**
- Заменить `anext(get_db())` на `db: AsyncSession = Depends(get_db)` в параметрах роута.
- Убрать прямой импорт `MeterRepository` из API-слоя.
- Использовать существующий use case или создать зависимость (Depends) для получения репозитория через `deps.py`, как в остальных модулях.
- **Решение владельца:** новый use case НЕ создавать — только исправить техническую ошибку.

**Проверка:** эндпоинт GET `/api/meters/` возвращает список счётчиков; тесты проходят.

---

### 1.2 Администратор не может закрыть право собственности

**Файлы:**
- `backend/app/modules/land_management/application/use_cases.py` — `ClosePlotOwnershipUseCase`
- `backend/app/modules/land_management/domain/repositories.py` — `IPlotOwnershipRepository`
- `backend/app/modules/land_management/infrastructure/repositories.py` — `PlotOwnershipRepository`
- `backend/app/modules/land_management/api/routes.py` — эндпоинт close_ownership

**Проблема:** У admin `cooperative_id = None`. Поиск записи с `cooperative_id = None` ничего не находит → admin получает 404.

**Что сделать:**
- Добавить метод `get_by_id_any_cooperative(id: UUID)` в `IPlotOwnershipRepository` (интерфейс) и в `PlotOwnershipRepository` (реализация).
- В `ClosePlotOwnershipUseCase`: если `cooperative_id is None` (admin) — использовать `get_by_id_any_cooperative`.
- **Решение владельца:** делать по аналогии с `DeleteLandPlotUseCase` и `GetLandPlotUseCase`.

**Проверка:** admin может закрыть право собственности; обычный пользователь — только в своём товариществе.

---

### 1.3 Контракт репозитория не совпадает с реализацией

**Файлы:**
- `backend/app/modules/land_management/domain/repositories.py` — `ILandPlotRepository`

**Проблема:** Метод `delete_by_id_any_cooperative` используется в коде, но отсутствует в интерфейсе.

**Что сделать:**
- Добавить `delete_by_id_any_cooperative(id: UUID) -> bool` в `ILandPlotRepository`.
- **Решение владельца:** делать одновременно с п.1.2 — оба интерфейса сразу.

**Проверка:** ruff check проходит; существующие тесты не ломаются.

---

### 1.4 Имена владельцев не видны при редактировании участка

**Файл:** `frontend/src/views/LandPlotEditView.vue`

**Проблема:** API возвращает только `owner_id` без `owner_name`. При загрузке формы поля владельцев пустые.

**Что сделать:**
- В `loadPlot()`: после получения данных участка, для каждого владельца сделать запрос `owners/{owner_id}` и заполнить `owner_name` и `searchQuery`.
- **Решение владельца:** вариант Б — правка только фронтенда, отдельные запросы за именами.

**Проверка:** при открытии редактирования участка отображаются имена текущих владельцев.

---

## Часть 2: ПРЕДУПРЕЖДЕНИЯ (архитектура и поведение)

### 2.1 Архитектурное нарушение в meters/use_cases.py

**Файл:** `backend/app/modules/meters/application/use_cases.py`

**Проблема:** Application-слой импортирует ORM-модели из infrastructure (`LandPlotModel`, `PlotOwnershipModel`).

**Что сделать:**
- Вынести логику определения cooperative по owner в метод репозитория (например, в `IOwnerRepository` или `IPlotOwnershipRepository`).
- Убрать импорт ORM-моделей из use case.
- **Решение владельца:** архитектура должна быть железной, исправлять обязательно.

**Проверка:** в `application/` ни одного файла нет импорта из `infrastructure/`.

---

### 2.2 Удаление участка — исправить описание эндпоинта

**Файл:** `backend/app/modules/land_management/api/routes.py` — эндпоинт delete_land_plot

**Проблема:** Описание говорит «Доступно только admin», но удалять может любой авторизованный.

**Что сделать:**
- Исправить описание (summary/description) эндпоинта: убрать «только admin».
- Проверку ролей НЕ добавлять — разграничение ролей будет позже.
- **Решение владельца:** удалять может казначей и председатель в рамках своего товарищества.

---

### 2.3 Событие `LandPlotCreated` дублируется в двух модулях

**Файлы:**
- `backend/app/modules/land_management/domain/events.py`
- `backend/app/modules/financial_core/domain/events.py`

**Проблема:** Один и тот же класс события описан в двух разных модулях. Обработчик подписан на одну версию, а публикуется другая.

**Что сделать:**
- Вынести общие (cross-module) события в `backend/app/modules/shared/kernel/events.py` (или создать `shared/domain/events.py`).
- Оставить в `land_management/domain/events.py` и `financial_core/domain/events.py` только события, специфичные для модуля.
- Все подписчики и публикаторы должны использовать один и тот же класс.
- **Решение владельца:** одна сущность — одно место. Мины замедленного действия не нужны.

**Проверка:** `LandPlotCreated` существует только в одном месте; grep по проекту подтверждает.

---

### 2.4 Поиск владельцев — общий таймер на все строки

**Файлы:**
- `frontend/src/views/LandPlotCreateView.vue`
- `frontend/src/views/LandPlotEditView.vue`

**Проблема:** Один `searchTimeout` на все строки. Быстрый ввод в разных строках отменяет поиск предыдущей.

**Что сделать:**
- Заменить один `searchTimeout` на массив/объект таймеров — по одному на каждую строку владельца.

---

### 2.5 Поиск в OwnersView — запрос при каждом нажатии клавиши

**Файл:** `frontend/src/views/OwnersView.vue`

**Что сделать:**
- Добавить debounce 300 мс на `onSearch`.

---

### 2.6 `checkAuth` — удалить неиспользуемую функцию

**Файл:** `frontend/src/stores/auth.ts`

**Что сделать:**
- Удалить функцию `checkAuth` и все связанные с ней экспорты/импорты.
- **Решение владельца:** убрать. Добавим позже, когда дойдём до активного тестирования.

---

### 2.7 Путь health — двойной `/api/api/health`

**Файл:** `frontend/src/stores/auth.ts`

**Что сделать:**
- Заменить `api.get('/api/health')` на `api.get('health')`.

---

### 2.8 Клик по строке таблицы участков — убрать `console.log`

**Файл:** `frontend/src/views/LandPlotsView.vue`

**Что сделать:**
- Удалить `handleRowClick` и `console.log`.
- Убрать кликабельность строки (если есть `@row-click` или аналог — удалить).
- Редактирование — только через кнопку с карандашом (уже есть).

---

## Часть 3: УБОРКА (мелочи)

**Статус раздела:** ✅ Выполнен

### ✅ 3.1 Удалить неиспользуемый `SessionDep`

**Файл:** `backend/app/modules/deps.py`

---

### ✅ 3.2 Исправить опечатку «coopérative»

**Файл:** `backend/app/modules/land_management/application/dtos.py` (строка ~52)

Заменить «ID coopérative» на «Cooperative ID» или «ID товарищества».

---

### ✅ 3.3 Заменить устаревший `asyncio.get_event_loop()`

**Файл:** `backend/app/modules/financial_core/infrastructure/event_handlers.py`

Заменить на `asyncio.create_task()` или другой актуальный подход.

---

### ✅ 3.4 Удалить `HelloWorld.vue`

**Файл:** `frontend/src/components/HelloWorld.vue`

Шаблонный компонент Vite, нигде не используется.

---

### ✅ 3.5 Удалить неиспользуемый CSS-класс `.share-input`

**Файл:** `frontend/src/views/LandPlotEditView.vue`

---

### ✅ 3.6 Исправить дублирование CSS-свойства `gap`

**Файл:** `frontend/src/views/LandPlotEditView.vue` (строки ~403–406)

Второе `gap: 12px` перезаписывает первое `gap: 12px 16px`. Оставить одно правильное значение.

---

### ✅ 3.7 Удалить неиспользуемую переменную `_emit`

**Файл:** `frontend/src/components/DataTable.vue`

---

### ✅ 3.8 Исправить замечания ruff (E402, I001)

24 замечания по порядку импортов в:
- `land_management/api/routes.py`
- `land_management/application/use_cases.py`
- `payment_distribution/tests/conftest.py`

Выполнить `ruff check . --fix` и при необходимости ручные правки.

---

## ОТДЕЛЬНАЯ ЗАДАЧА (НЕ входит в этот план)

### Дизайн-система: приведение цветов к единой теме

**Не включать в текущий план.** Создать отдельную задачу:
- Зелёные цвета в `LoginView.vue` при общей indigo-теме
- Жёстко зашитые цвета вместо CSS-переменных в нескольких Vue-файлах
- Проверка `DataTable.vue` — класс `clickable` и `$attrs.onRowClick`

---

## Усиление архитектурных правил

**Дополнительно (по решению владельца):** после всех исправлений проверить и при необходимости усилить описания архитектурных правил в `.cursor/rules/`, чтобы агенты в будущем не нарушали границы слоёв. В частности:
- Явно указать, что `application/` НЕ может импортировать из `infrastructure/`
- Явно указать, что `api/` НЕ может импортировать из `infrastructure/` (только через Depends и use cases)
- Добавить пример правильного и неправильного импорта

---

## Порядок выполнения

1. Создать ветку `feature/audit-fixes-20260317` от `feature/2026-03-15-session`
2. **Критичные (Часть 1):** п.1.1 → 1.2 + 1.3 → 1.4
3. **Предупреждения (Часть 2):** п.2.1 → 2.3 → 2.2 → 2.4 → 2.5 → 2.6 → 2.7 → 2.8
4. **Уборка (Часть 3):** п.3.1–3.8 — ✅ выполнено
5. Усиление архитектурных правил
6. **Проверки перед завершением:**
   - `pytest` — все тесты проходят
   - `ruff check .` — 0 ошибок
   - `ruff format --check .` — OK
   - `python -m app.scripts.seed_db` — без ошибок
   - Ревью @architecture-guardian (архитектурные изменения в п.2.1, 2.3)
7. Обновить `docs/plan/current-focus.md`

---

## Результат (result) — проверки перед merge в main

**Дата проверки:** 2026-03-17  
**Проверено:** агент Architecture Guardian + границы слоёв по коду

### Вопросы проверки

1. **Сломали ли изменения архитектуру?** — Нет.
2. **Соблюдены ли требования по разделению зон ответственности по слоям?** — Да.

### Чек-лист Architecture Guardian

| Пункт | Статус |
|--------|--------|
| API не импортирует из infrastructure | ✅ OK |
| Application не импортирует из infrastructure | ✅ OK |
| Domain только stdlib / shared kernel | ✅ OK |
| Финансовое ядро (Accrual/Payment через FinancialSubject; нет hard delete по задаче) | ✅ OK |
| Модель данных / контракты репозиториев согласованы | ✅ OK |
| События (LandPlotCreated, MeterCreated) в одном месте — shared/domain/events.py | ✅ OK |
| Описание эндпоинта delete_land_plot, SessionDep, опечатка coopérative, asyncio | ✅ OK |
| Ruff check | ✅ All checks passed |

### Выводы

- **Границы слоёв:** Роуты meters и land_management получают репозитории и use case только через `Depends` из `deps.py`. В `application/` нет импортов из `infrastructure/`; определение cooperative_id перенесено в репозиторий (методы `get_cooperative_id_by_owner_id`, `get_cooperative_id_by_meter_id`).
- **События:** Общие события вынесены в `backend/app/modules/shared/domain/events.py`; модули только реэкспортируют или импортируют из shared. Дублирования нет.
- **Контракты:** В интерфейсы добавлены `delete_by_id_any_cooperative` (ILandPlotRepository) и `get_by_id_any_cooperative` (IPlotOwnershipRepository); реализации есть в infrastructure.

**Вердикт:** С точки зрения архитектуры и разделения ответственности по слоям **ветку можно мержить в main** после твоего одобрения.

**Рекомендация перед merge:** один раз выполнить полный прогон `pytest` в backend и при необходимости `ruff format --check .`, затем утвердить этот результат и выполнить merge на GitHub.

---

*Создано: 2026-03-17 по результатам аудита*
