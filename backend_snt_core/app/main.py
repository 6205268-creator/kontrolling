from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.router import api_router

app = FastAPI(title="SNT Accounting Core")

app.include_router(api_router)


@app.get("/health")
def health_check() -> dict:
    """Простейшая проверка живости backend ядра."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>СНТ — ядро учёта</title>
    <style>
      :root { --fg:#111; --muted:#555; --bg:#fff; --card:#f6f7f9; --border:#e5e7eb; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; color: var(--fg); background: var(--bg); }
      h1 { margin: 0 0 8px; }
      p { margin: 6px 0; color: var(--muted); }
      .row { display:flex; gap: 16px; flex-wrap: wrap; align-items: flex-start; }
      .card { background: var(--card); border:1px solid var(--border); border-radius: 12px; padding: 14px; min-width: 320px; }
      .card h2 { margin: 0 0 10px; font-size: 16px; }
      label { display:block; font-size: 12px; color: var(--muted); margin: 8px 0 4px; }
      input, select, textarea { width: 100%; box-sizing: border-box; border:1px solid var(--border); border-radius: 10px; padding: 10px; background:#fff; }
      textarea { min-height: 110px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
      button { border:1px solid var(--border); background:#111; color:#fff; padding: 10px 12px; border-radius: 10px; cursor:pointer; }
      button.secondary { background:#fff; color:#111; }
      .btns { display:flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
      .ok { color: #0a7a25; }
      .err { color: #b42318; }
      a { color:#1f4b99; text-decoration:none; }
      a:hover { text-decoration: underline; }
      small { color: var(--muted); }
      pre { background:#0b1220; color:#d8dee9; padding: 10px; border-radius: 10px; overflow:auto; }
    </style>
  </head>
  <body>
    <h1>Система учёта СНТ (ядро)</h1>
    <p>Это простая страница поверх REST API. Логика/проведение — только в backend/БД.</p>
    <p>
      Ссылки: <a href="/docs">Swagger</a> · <a href="/openapi.json">OpenAPI</a> · <a href="/health">Health</a>
    </p>

    <div class="row">
      <div class="card">
        <h2>1) СНТ (tenant)</h2>
        <div class="btns">
          <button class="secondary" onclick="loadSnts()">Обновить список</button>
        </div>
        <label>Текущее СНТ</label>
        <select id="sntSelect"></select>

        <label>Создать СНТ</label>
        <input id="sntName" placeholder="Например: СНТ Берёзка" />
        <div class="btns">
          <button onclick="createSnt()">Создать</button>
        </div>
        <small>Все остальные операции завязаны на выбранный <span class="mono">snt_id</span>.</small>
      </div>

      <div class="card">
        <h2>2) Справочники</h2>
        <label>Участки</label>
        <div class="btns">
          <button class="secondary" onclick="listPlots()">Список участков</button>
          <button onclick="createPlot()">Добавить участок</button>
        </div>
        <input id="plotNumber" placeholder="Номер участка (например 12)" />

        <label>Собственники</label>
        <div class="btns">
          <button class="secondary" onclick="listOwners()">Список собственников</button>
          <button onclick="createOwner()">Добавить собственника</button>
        </div>
        <input id="ownerName" placeholder="ФИО (например Иванов Иван Иванович)" />

        <label>Статьи</label>
        <div class="btns">
          <button class="secondary" onclick="listChargeItems()">Список статей</button>
          <button onclick="createChargeItem()">Добавить статью</button>
        </div>
        <input id="chargeItemName" placeholder="Название (например Членский взнос)" />
        <input id="chargeItemType" placeholder="type (например membership)" />
      </div>

      <div class="card">
        <h2>3) Документы</h2>
        <small>Вставляй JSON как в Swagger. Для начисления требуется <span class="mono">owner_id</span> в строке.</small>

        <label>Создать начисление (POST /documents/accruals)</label>
        <textarea id="accrualJson" class="mono">{
  "number": "A-TEST-1",
  "date": "2026-01-01",
  "rows": [
    { "plot_id": 1, "owner_id": 1, "charge_item_id": 1, "amount": 1500, "period_from": "2026-01-01", "period_to": "2026-01-31" }
  ]
}</textarea>
        <div class="btns">
          <button onclick="createAccrual()">Создать начисление</button>
          <button class="secondary" onclick="listAccruals()">Список начислений</button>
          <button class="secondary" onclick="postAccrual()">Провести по id</button>
          <button class="secondary" onclick="unpostAccrual()">Отменить по id</button>
        </div>
        <input id="accrualId" placeholder="id начисления для (от)проведения" />

        <label>Создать оплату (POST /documents/payments)</label>
        <textarea id="paymentJson" class="mono">{
  "number": "P-TEST-1",
  "date": "2026-01-10",
  "rows": [
    { "plot_id": 1, "owner_id": 1, "charge_item_id": 1, "amount": 1000 }
  ]
}</textarea>
        <div class="btns">
          <button onclick="createPayment()">Создать оплату</button>
          <button class="secondary" onclick="listPayments()">Список оплат</button>
          <button class="secondary" onclick="postPayment()">Провести по id</button>
          <button class="secondary" onclick="unpostPayment()">Отменить по id</button>
        </div>
        <input id="paymentId" placeholder="id оплаты для (от)проведения" />
      </div>

      <div class="card">
        <h2>4) Отчёт</h2>
        <label>Сальдо на дату (GET /reports/balance)</label>
        <input id="balanceDate" value="2026-01-31" />
        <div class="btns">
          <button class="secondary" onclick="getBalance()">Получить сальдо</button>
        </div>
      </div>
    </div>

    <h2>Вывод</h2>
    <pre id="out">Нажми кнопку — здесь появится ответ API.</pre>

    <script>
      const out = document.getElementById('out');
      const sntSelect = document.getElementById('sntSelect');
      function sntId() {
        const v = sntSelect.value;
        if (!v) throw new Error('Выбери или создай СНТ');
        return Number(v);
      }
      function show(obj, ok=true) {
        out.textContent = (ok ? '' : 'ERROR\\n') + JSON.stringify(obj, null, 2);
        out.className = ok ? 'ok' : 'err';
      }
      async function api(method, path, body) {
        const opts = { method, headers: { 'Content-Type': 'application/json' } };
        if (body !== undefined) opts.body = JSON.stringify(body);
        const r = await fetch(path, opts);
        let data;
        try { data = await r.json(); } catch { data = await r.text(); }
        if (!r.ok) throw { status: r.status, data };
        return data;
      }
      async function loadSnts() {
        try {
          const data = await api('GET', '/snts');
          sntSelect.innerHTML = '';
          for (const s of data) {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `#${s.id} — ${s.name}`;
            sntSelect.appendChild(opt);
          }
          show(data);
        } catch (e) { show(e, false); }
      }
      async function createSnt() {
        try {
          const name = document.getElementById('sntName').value.trim();
          const data = await api('POST', '/snts', { name });
          await loadSnts();
          sntSelect.value = String(data.id);
          show(data);
        } catch (e) { show(e, false); }
      }

      async function listPlots(){ try { show(await api('GET', `/snts/${sntId()}/plots`)); } catch(e){ show(e,false);} }
      async function createPlot(){ try { show(await api('POST', `/snts/${sntId()}/plots`, { number: document.getElementById('plotNumber').value.trim() })); } catch(e){ show(e,false);} }
      async function listOwners(){ try { show(await api('GET', `/snts/${sntId()}/owners`)); } catch(e){ show(e,false);} }
      async function createOwner(){ try { show(await api('POST', `/snts/${sntId()}/owners`, { full_name: document.getElementById('ownerName').value.trim() })); } catch(e){ show(e,false);} }
      async function listChargeItems(){ try { show(await api('GET', `/snts/${sntId()}/charge-items`)); } catch(e){ show(e,false);} }
      async function createChargeItem(){
        try {
          show(await api('POST', `/snts/${sntId()}/charge-items`, { name: document.getElementById('chargeItemName').value.trim(), type: document.getElementById('chargeItemType').value.trim() }));
        } catch(e){ show(e,false);}
      }

      async function createAccrual(){
        try { show(await api('POST', `/snts/${sntId()}/documents/accruals`, JSON.parse(document.getElementById('accrualJson').value))); } catch(e){ show(e,false);}
      }
      async function listAccruals(){ try { show(await api('GET', `/snts/${sntId()}/documents/accruals`)); } catch(e){ show(e,false);} }
      async function postAccrual(){ try { show(await api('POST', `/snts/${sntId()}/documents/accruals/${Number(document.getElementById('accrualId').value)}/post`)); } catch(e){ show(e,false);} }
      async function unpostAccrual(){ try { show(await api('POST', `/snts/${sntId()}/documents/accruals/${Number(document.getElementById('accrualId').value)}/unpost`)); } catch(e){ show(e,false);} }

      async function createPayment(){
        try { show(await api('POST', `/snts/${sntId()}/documents/payments`, JSON.parse(document.getElementById('paymentJson').value))); } catch(e){ show(e,false);}
      }
      async function listPayments(){ try { show(await api('GET', `/snts/${sntId()}/documents/payments`)); } catch(e){ show(e,false);} }
      async function postPayment(){ try { show(await api('POST', `/snts/${sntId()}/documents/payments/${Number(document.getElementById('paymentId').value)}/post`)); } catch(e){ show(e,false);} }
      async function unpostPayment(){ try { show(await api('POST', `/snts/${sntId()}/documents/payments/${Number(document.getElementById('paymentId').value)}/unpost`)); } catch(e){ show(e,false);} }

      async function getBalance(){
        try {
          const d = document.getElementById('balanceDate').value;
          show(await api('GET', `/snts/${sntId()}/reports/balance?on_date=${encodeURIComponent(d)}`));
        } catch(e){ show(e,false);}
      }

      loadSnts();
    </script>
  </body>
</html>
"""

