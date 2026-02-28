# Memory Bank Instructions

## 🤖 Инструкции для AI-ассистента

### Что такое Memory Bank

**Memory Bank** — это система из 7 документов, которая сохраняет контекст проекта для AI-ассистента (Cursor, Cline, etc.).

**Цель**: AI понимает проект с первого сообщения, не задаёт лишних вопросов, предлагает релевантные решения.

---

## 📁 Структура Memory Bank

```
.memory-bank/
├── projectbrief.md           # Что делает проект
├── productContext.md         # Почему проект существует
├── activeContext.md          # Что сейчас в работе
├── systemPatterns.md         # Архитектурные паттерны
├── techContext.md            # Технологии и инструменты
├── progress.md               # Что сделано / что осталось
└── memory_bank_instructions.md # Этот файл
```

---

## 🎯 Когда использовать

### Перед началом сессии

**Прочитай**:
1. `activeContext.md` — что сейчас в работе, какие задачи
2. `progress.md` — что уже сделано, что планируется

**Пойми**:
- На какой фазе проект
- Какие задачи в приоритете
- Есть ли блокеры

---

### При работе с кодом

**Используй**:
1. `systemPatterns.md` — архитектурные паттерны, conventions
2. `techContext.md` — технологии, зависимости, инструменты

**Следуй**:
- Clean Architecture (backend)
- Composition API (frontend)
- Repository pattern
- Dependency Injection

---

### При работе с архитектурой

**Используй**:
1. `productContext.md` — зачем проект, какие проблемы решает
2. `systemPatterns.md` — текущие паттерны

**Предлагай**:
- Решения в рамках текущей архитектуры
- Улучшения, которые не ломают существующие паттерны

---

## 🔧 MCP Commands

Если установлен MCP Memory Bank сервер:

### Чтение контекста

```
/memory-bank read activeContext — что сейчас в работе
/memory-bank read progress — что сделано
/memory-bank read systemPatterns — архитектура
```

### Обновление прогресса

```
/memory-bank update progress — записать что сделано за сессию
/memory-bank update activeContext — обновить текущие задачи
```

### Анализ проекта

```
/memory-bank analyze — предложить улучшения для Memory Bank
```

---

## 📝 Conventions

### Стиль кода (Backend)

- **Имена**: глаголы для функций, существительные для переменных
- **Поток**: guard clauses, ранний return
- **Комментарии**: только «почему», не «как»
- **Форматирование**: Black, ruff

### Стиль кода (Frontend)

- **Компоненты**: Composition API (`<script setup>`)
- **Stores**: Pinia
- **Типы**: TypeScript strict mode
- **Форматирование**: Prettier

---

## 🧭 Workflow

### Для нетривиальных задач (3+ шага)

1. **План** → `tasks/todo.md` (checkable items)
2. **Check-in** → перед реализацией
3. **Реализация** → по шагам
4. **Верификация** → тесты, логи, демонстрация
5. **Review** → `tasks/todo.md` секция review
6. **Уроки** → `tasks/lessons.md`

**Полный текст**: [`tasks/workflow-orchestration.md`](../tasks/workflow-orchestration.md)

---

## 🎓 Cursor Rules

Проект использует **выборочную загрузку правил** Cursor:

### Корень (всегда применяются)

- `communication-style.mdc` — стиль общения
- `guide-workflow.mdc` — «вопрос ≠ действие»
- `project-conventions.mdc` — конвенции проекта

### Plan (при работе с tasks/)

- `workflow-orchestration.mdc` — планирование задач

### Architecture (при работе с docs/, *.mmd, *.bpmn)

- `architecture-rules.mdc` — Mermaid, именование
- `aac-c4-architecture.mdc` — C4 Model
- `bpmn-process-rules.mdc` — BPMN процессы
- `bpmn-viewer-show.mdc` — показ BPMN в браузере
- `schema-viewer-show.mdc` — показ схемы данных

### Build (при работе с backend/, frontend/)

- `code-style-and-tools.mdc` — стиль кода, инструменты
- `context7-docs.mdc` — документация библиотек (Context7)
- `backend-testing-and-pitfalls.mdc` — тесты backend

**Путь**: `.cursor/rules/`

---

## 🚀 Быстрый старт для AI

**Первое сообщение в новой сессии**:

> «Привет! Я работаю над проектом КОНТРОЛЛИНГ — система учёта для СТ.
> 
> **Текущая задача**: [описание задачи]
> 
> **Контекст**:
> - Backend: Clean Architecture, FastAPI, SQLAlchemy
> - Frontend: Vue 3, Pinia, TypeScript
> - Тесты: 192 passed
> 
> **Что нужно**: [конкретная просьба]»

**AI прочитает**:
- `activeContext.md` → поймёт текущие задачи
- `systemPatterns.md` → предложит архитектурно-правильное решение
- `techContext.md` → даст релевантные примеры кода

---

## 📊 Обновление Memory Bank

### После каждой сессии

**Обнови `activeContext.md`**:
- Что сделано
- Что планируется дальше
- Новые блокеры (если есть)

**Обнови `progress.md`**:
- Добавь запись в «Историю прогресса»
- Обнови метрики

### При изменении архитектуры

**Обнови `systemPatterns.md`**:
- Новые паттерны
- Изменения в существующих

**Обнови `techContext.md`**:
- Новые зависимости
- Изменения в инструментах

---

## 💡 Советы

### Для пользователя

1. **Перед сессией**: кратко опиши задачу + ссылку на контекст
2. **Во время сессии**: задавай уточняющие вопросы по архитектуре
3. **После сессии**: обнови `activeContext.md` (что сделано)

### для AI-ассистента

1. **Всегда проверяй** `activeContext.md` перед началом
2. **Следуй паттернам** из `systemPatterns.md`
3. **Используй Context7** для документации библиотек
4. **Предлагай план** для задач 3+ шагов
5. **Верифицируй** результат (тесты, логи, демонстрация)

---

## 🔗 Связанные документы

- **Workflow**: [`tasks/workflow-orchestration.md`](../tasks/workflow-orchestration.md)
- **Cursor Rules**: [`.cursor/rules/`](../.cursor/rules/)
- **Архитектура**: [`docs/architecture/`](../docs/architecture/)

---

*Последнее обновление: 28 февраля 2026*
