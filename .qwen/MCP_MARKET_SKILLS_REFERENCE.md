# Рекомендуемые навыки MCP Market для проекта

Каталог: **[mcpmarket.com/tools/skills](https://mcpmarket.com/tools/skills)**

Навыки на MCP Market ориентированы на **Claude** (формат SKILL.md). Для **Qwen/Gwen** их можно использовать как образец: идеи и структура переносятся в `.qwen/skills/*.md` (YAML frontmatter + markdown).

---

## Для выполнения плана «Single development index and roadmap»

| Навык | Ссылка | Зачем |
|-------|--------|--------|
| **Doc Co-Authoring** | [mcpmarket.com/tools/skills/doc-co-authoring](https://mcpmarket.com/tools/skills/doc-co-authoring) | Структурированный 3-этапный процесс (Context → Refinement → Reader Testing) для написания сложной документации; полезен при создании секций `docs/development-index.md` (Этап 4). |
| **Project Blueprint & Guidelines Template** | [mcpmarket.com/tools/skills/project-blueprint-guidelines-template](https://mcpmarket.com/tools/skills/project-blueprint-guidelines-template) | Фреймворк для архитектуры проекта, паттернов, тестов и деплоя — по смыслу близко к «единой точке входа» и индексу. |
| **Architecture Decision Records** | [mcpmarket.com/tools/skills/architecture-decision-records](https://mcpmarket.com/tools/skills/architecture-decision-records) | Стандартизированный формат ADR; в плане есть DECISIONS_LOG, RESOLVED_GAPS, adr/ — навык помогает держать единый стиль записей. |
| **Coding Agent Orchestrator** | [mcpmarket.com/tools/skills/coding-agent-orchestrator-1](https://mcpmarket.com/tools/skills/coding-agent-orchestrator-1) | Делегирование сложных задач по этапам; можно использовать как образец для «выполнять по одному этапу за сессию». |
| **Create Skill File** | [mcpmarket.com/tools/skills/create-skill-file](https://mcpmarket.com/tools/skills/create-skill-file) | Создание SKILL.md по стандарту; полезно, если Qwen будет дополнять `.qwen/skills/` под новые сценарии. |

---

## Дополнительно (Learning & Documentation)

Категория: **[Learning & Documentation](https://mcpmarket.com/tools/skills/categories/learning-documentation)** — 86+ навыков.

- **Context7 Documentation Lookup** — актуальная документация по библиотекам (в проекте уже есть Context7 MCP в `.cursor/mcp.json`).
- **Changelog Automation** — генерация changelog из git; пригодится после больших консолидаций (Этап 3).
- **Next.js Documentation Updater** — идея «синхронизация доков с кодом»; аналог для нашего индекса — обновлять ссылки после переносов.

---

## Локальные навыки проекта (Qwen)

| Файл | Назначение |
|------|------------|
| `.qwen/skills/plan-execution-docs-consolidation.md` | Выполнение плана по этапам, обновление ссылок, чеклист, без выдумывания контента. |
| `.qwen/skills/vue-development.md` | Vue 3 / фронтенд; для плана индекса не обязателен. |

При запуске плана подключать **plan-execution-docs-consolidation**; при необходимости брать структуру/идеи из навыков MCP Market выше.

---

## Совместимость: не противоречат друг другу

Подключать все перечисленные навыки вместе **можно** — они не конфликтуют, потому что срабатывают в разных ситуациях:

| Ситуация | Какой навык в приоритете | Остальные |
|----------|---------------------------|-----------|
| «Выполни план», консолидация доков | **plan-execution-docs-consolidation** — чеклист и этапы главнее | Doc Co-Authoring/Blueprint/ADR — только как образец формата (например, для секций индекса или записей в RESOLVED_GAPS) |
| Задача по Vue/фронту, компоненты, тесты | **vue-development** | Остальные не про код — не мешают |
| Написание новой документации (не по плану) | Doc Co-Authoring, ADR, Blueprint — по смыслу задачи | plan-execution не срабатывает («execute the plan» не было) |
| Создание нового навыка (SKILL.md) | **Create Skill File** | Остальные про контент/план — не пересекаются |

**Язык ответов:** задаёт проект (AGENTS.md / QWEN.md: русский). Навыки описывают *как* делать (этапы, форматы, красные флаги), а не «отвечать на языке X» — противоречия нет.

**Итог:** можно подключать все; агент будет выбирать навык по типу задачи, а не применять все правила одновременно к одному действию.
