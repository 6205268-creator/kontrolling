# Промпт для новой сессии (скопировать в чат агента)

Скопируй блок ниже **целиком**.

---

## Текст промпта (русский)

Ты работаешь в репозитории **Controlling**. Прочитай и следуй техническому заданию:

`docs/scenario/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md`

Уже создано (не выдумывай заново без необходимости):

- Матрица года: `docs/scenario/life-year-matrix.md` (EVT-001…EVT-024, статусы сверены с кодом на момент создания; **перепроверь** статусы после изменений в backend/frontend).
- Пример «выписки»: `docs/scenario/files/bank-2024-05-05-sample.csv`
- Этот промпт: `docs/scenario/PROMPT-new-session.md`

**Правила**

1. **Не придумывай** бизнес-правила (порядок погашения взносов, штрафы, виды начислений), если их нет в документах владельца или в ADR/ТЗ модулей.
2. **Сверяй** эндпоинты и экраны с **фактическим кодом** (`backend/app/modules`, `frontend/src`), не с памятью модели.
3. **Фаза A (приоритет):** поддерживать матрицу в актуальном состоянии: колонки статусов, дыры, связи с модулями. Новые жизненные кейсы — **новые EVT-ID**, старые ID не переиспользовать под другое значение.
4. **Фаза B:** раннер (Playwright + HTTP, профили `validate` / `smoke` / `full` / `interactive`, логи `summary.json` + `steps.jsonl`, субтитры **отдельно** от UI Controlling) — только после стабилизации строк со статусом `реализовано` или осмысленным `частично`, и по отдельной команде владельца.
5. Деньги в домене — **BYN**.

**Задача сессии** (выбери по запросу пользователя или спроси):

- обновить статусы в `life-year-matrix.md` после аудита API/UI;
- расширить матрицу (новые EVT) по замечаниям казначея;
- начать/продолжить реализацию раннера по §7 ТЗ;
- подготовить smoke-цепочку по EVT с тегом `smoke` в матрице.

---

## Short English (optional)

Work in repo **Controlling**. Read `docs/scenario/TECHNICAL-SPEC-life-scenario-matrix-and-runner.md`. Matrix: `docs/scenario/life-year-matrix.md`. Do not invent business rules; verify API/UI against code. Phase A = maintain matrix; Phase B = runner per spec, on owner request. Currency BYN.

---

*Версия промпта: 1.0 (2026-03-20).*
