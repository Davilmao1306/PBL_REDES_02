from __future__ import annotations


DASHBOARD_HTML = r"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Drone Mesh Dashboard</title>
  <style>
    :root {
      --bg: #f4f5f2;
      --panel: #ffffff;
      --ink: #1f2428;
      --muted: #667085;
      --line: #d7dbd2;
      --green: #18895b;
      --red: #c63d32;
      --amber: #b7791f;
      --teal: #0f766e;
      --violet: #635bff;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-width: 320px;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    button,
    input,
    select {
      font: inherit;
    }

    .app {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .topbar {
      border-bottom: 1px solid var(--line);
      background: #fbfcfa;
    }

    .topbar-inner {
      width: min(1480px, calc(100vw - 32px));
      margin: 0 auto;
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }

    .brand {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .brand h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.15;
      font-weight: 760;
    }

    .brand span {
      color: var(--muted);
      font-size: 13px;
    }

    .top-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .btn {
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--ink);
      padding: 0 12px;
      cursor: pointer;
    }

    .btn:hover {
      border-color: #9aa39a;
    }

    .btn-primary {
      color: #ffffff;
      border-color: var(--teal);
      background: var(--teal);
    }

    main {
      width: min(1480px, calc(100vw - 32px));
      margin: 18px auto 28px;
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(5, minmax(150px, 1fr));
      gap: 12px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 14px;
      min-height: 96px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 10px;
    }

    .metric-label,
    .section-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 720;
    }

    .metric-value {
      font-size: 28px;
      line-height: 1;
      font-weight: 760;
    }

    .metric small {
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(360px, 0.85fr);
      gap: 14px;
      align-items: start;
    }

    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      overflow: hidden;
    }

    .panel-header {
      min-height: 54px;
      padding: 12px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid var(--line);
    }

    .panel-header h2 {
      margin: 0;
      font-size: 15px;
      line-height: 1.25;
    }

    .panel-body {
      padding: 14px;
    }

    .grid-two {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .broker-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(130px, 1fr));
      gap: 10px;
    }

    .broker-node {
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 102px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 8px;
      background: #fbfbf8;
    }

    .broker-node.active {
      border-color: rgba(24, 137, 91, 0.45);
      background: #f3fbf6;
    }

    .broker-node.down {
      border-color: rgba(198, 61, 50, 0.38);
      background: #fff7f5;
    }

    .broker-node.local {
      box-shadow: inset 0 0 0 2px rgba(99, 91, 255, 0.22);
    }

    .node-name {
      font-weight: 760;
      line-height: 1.2;
    }

    .node-url {
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 0 9px;
      font-size: 12px;
      font-weight: 720;
      border: 1px solid var(--line);
      background: #f6f7f3;
      white-space: nowrap;
    }

    .badge.green {
      color: var(--green);
      border-color: rgba(24, 137, 91, 0.32);
      background: #edf9f1;
    }

    .badge.red {
      color: var(--red);
      border-color: rgba(198, 61, 50, 0.30);
      background: #fff0ed;
    }

    .badge.amber {
      color: var(--amber);
      border-color: rgba(183, 121, 31, 0.32);
      background: #fff8e6;
    }

    .badge.violet {
      color: var(--violet);
      border-color: rgba(99, 91, 255, 0.28);
      background: #f3f1ff;
    }

    .table-wrap {
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 660px;
    }

    th,
    td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: middle;
      font-size: 13px;
    }

    th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 720;
      background: #fbfbf8;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .mono {
      font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .queue-list,
    .events-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .queue-item,
    .event-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fbfbf8;
      display: grid;
      gap: 8px;
    }

    .queue-title,
    .event-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }

    .queue-title strong,
    .event-title strong {
      overflow-wrap: anywhere;
    }

    .queue-meta,
    .event-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      color: var(--muted);
      font-size: 12px;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 720;
      text-transform: uppercase;
    }

    input,
    select {
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 10px;
      color: var(--ink);
      background: #ffffff;
    }

    .full {
      grid-column: 1 / -1;
    }

    .message {
      min-height: 20px;
      color: var(--muted);
      font-size: 13px;
    }

    .empty {
      color: var(--muted);
      font-size: 13px;
      padding: 16px 0;
    }

    @media (max-width: 1080px) {
      .metrics {
        grid-template-columns: repeat(2, minmax(150px, 1fr));
      }

      .layout,
      .grid-two {
        grid-template-columns: 1fr;
      }

      .broker-grid {
        grid-template-columns: repeat(2, minmax(130px, 1fr));
      }
    }

    @media (max-width: 640px) {
      .topbar-inner,
      main {
        width: min(100vw - 20px, 1480px);
      }

      .topbar-inner {
        align-items: flex-start;
        flex-direction: column;
        padding: 14px 0;
      }

      .top-actions {
        width: 100%;
        justify-content: stretch;
      }

      .top-actions .btn {
        flex: 1;
      }

      .metrics,
      .broker-grid,
      .form-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <h1>Drone Mesh Dashboard</h1>
          <span id="subtitle">Conectando ao broker...</span>
        </div>
        <div class="top-actions">
          <span class="badge" id="connectionStatus">Atualizando</span>
          <button class="btn" id="pauseButton" type="button">Pausar</button>
          <button class="btn btn-primary" id="refreshButton" type="button">Atualizar</button>
        </div>
      </div>
    </header>

    <main>
      <section class="metrics" aria-label="Resumo">
        <div class="metric">
          <span class="metric-label">Broker local</span>
          <strong class="metric-value" id="localBroker">-</strong>
          <small id="localUrl">-</small>
        </div>
        <div class="metric">
          <span class="metric-label">Coordenador</span>
          <strong class="metric-value" id="coordinator">-</strong>
          <small>menor ID ativo</small>
        </div>
        <div class="metric">
          <span class="metric-label">Brokers ativos</span>
          <strong class="metric-value" id="activeCount">0</strong>
          <small id="activeList">-</small>
        </div>
        <div class="metric">
          <span class="metric-label">Drones livres</span>
          <strong class="metric-value" id="availableDrones">0</strong>
          <small id="droneSummary">-</small>
        </div>
        <div class="metric">
          <span class="metric-label">Fila pendente</span>
          <strong class="metric-value" id="pendingCount">0</strong>
          <small>prioridade, Lamport, broker</small>
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <h2>Brokers</h2>
          <span class="badge" id="lastUpdated">-</span>
        </div>
        <div class="panel-body">
          <div class="broker-grid" id="brokersGrid"></div>
        </div>
      </section>

      <div class="layout">
        <div class="panel">
          <div class="panel-header">
            <h2>Ocorrencias</h2>
            <span class="badge" id="occurrenceCount">0 itens</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Status</th>
                  <th>Prioridade</th>
                  <th>Lamport</th>
                  <th>Broker</th>
                  <th>Drone</th>
                </tr>
              </thead>
              <tbody id="occurrencesTable"></tbody>
            </table>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h2>Fila distribuida</h2>
            <span class="badge amber" id="queueCount">0 pendentes</span>
          </div>
          <div class="panel-body">
            <ul class="queue-list" id="queueList"></ul>
          </div>
        </div>
      </div>

      <div class="layout">
        <div class="panel">
          <div class="panel-header">
            <h2>Drones</h2>
            <span class="badge" id="droneCount">0 itens</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Drone</th>
                  <th>Status</th>
                  <th>Broker</th>
                  <th>Ocorrencia</th>
                  <th>Callback</th>
                </tr>
              </thead>
              <tbody id="dronesTable"></tbody>
            </table>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h2>Nova ocorrencia</h2>
            <span class="badge violet">Teste manual</span>
          </div>
          <div class="panel-body">
            <form id="occurrenceForm" class="form-grid">
              <label>
                Setor
                <select id="sectorInput">
                  <option value="1">Setor 1</option>
                  <option value="2">Setor 2</option>
                  <option value="3">Setor 3</option>
                  <option value="4">Setor 4</option>
                </select>
              </label>
              <label>
                Prioridade
                <select id="severityInput">
                  <option value="5">5 - Critica</option>
                  <option value="4">4 - Alta</option>
                  <option value="3">3 - Media</option>
                  <option value="2">2 - Baixa</option>
                  <option value="1">1 - Minima</option>
                </select>
              </label>
              <label class="full">
                Descricao
                <input id="descriptionInput" value="ocorrencia manual pelo dashboard">
              </label>
              <button class="btn btn-primary full" type="submit">Criar ocorrencia</button>
              <div class="message full" id="formMessage"></div>
            </form>
          </div>
        </div>
      </div>

      <section class="panel">
        <div class="panel-header">
          <h2>Eventos recentes</h2>
          <span class="badge" id="eventCount">0 eventos</span>
        </div>
        <div class="panel-body">
          <ul class="events-list" id="eventsList"></ul>
        </div>
      </section>
    </main>
  </div>

  <script>
    const state = {
      paused: false,
      timer: null,
      lastState: null
    };

    const $ = (id) => document.getElementById(id);

    function statusBadge(status) {
      const normalized = String(status || "-").toLowerCase();
      let klass = "";
      if (["available", "done", "active"].includes(normalized)) klass = "green";
      if (["offline", "down"].includes(normalized)) klass = "red";
      if (["pending", "reserved", "busy", "assigned"].includes(normalized)) klass = "amber";
      return `<span class="badge ${klass}">${escapeHtml(status || "-")}</span>`;
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function fmtTime(value) {
      if (!value) return "-";
      return new Date(value * 1000).toLocaleTimeString();
    }

    function brokerExternalUrl(id) {
      const port = 8000 + Number(id);
      return `http://localhost:${port}`;
    }

    function render(data) {
      state.lastState = data;
      const occurrences = data.occurrences || [];
      const drones = data.drones || [];
      const pending = data.pending_queue || [];
      const active = data.active_brokers || [];
      const known = data.known_brokers || {};
      const events = data.events || [];

      $("subtitle").textContent = `${data.broker_url} | Lamport ${data.lamport_ts ?? "-"}`;
      $("localBroker").textContent = data.broker_id ?? "-";
      $("localUrl").textContent = data.broker_url ?? "-";
      $("coordinator").textContent = data.coordinator_id ?? "-";
      $("activeCount").textContent = active.length;
      $("activeList").textContent = active.length ? active.map((id) => `broker-${id}`).join(", ") : "-";
      $("availableDrones").textContent = drones.filter((item) => item.status === "available").length;
      $("droneSummary").textContent = `${drones.length} registrados`;
      $("pendingCount").textContent = pending.length;
      $("lastUpdated").textContent = new Date().toLocaleTimeString();
      $("occurrenceCount").textContent = `${occurrences.length} itens`;
      $("queueCount").textContent = `${pending.length} pendentes`;
      $("droneCount").textContent = `${drones.length} itens`;
      $("eventCount").textContent = `${events.length} eventos`;

      renderBrokers(data, known, active);
      renderOccurrences(occurrences);
      renderQueue(pending);
      renderDrones(drones);
      renderEvents(events);
      setConnection("online");
    }

    function renderBrokers(data, known, active) {
      const ids = new Set([1, 2, 3, 4, ...Object.keys(known).map(Number), ...(active || [])]);
      $("brokersGrid").innerHTML = [...ids].sort((a, b) => a - b).map((id) => {
        const isActive = active.includes(id);
        const isLocal = Number(data.broker_id) === Number(id);
        const isCoordinator = Number(data.coordinator_id) === Number(id);
        const peer = (data.peer_status || {})[id] || {};
        const url = known[id] || `broker-${id}`;
        const classes = ["broker-node", isActive ? "active" : "down", isLocal ? "local" : ""].join(" ");
        return `
          <article class="${classes}">
            <div>
              <div class="node-name">broker-${id}</div>
              <div class="node-url">${escapeHtml(url)}</div>
            </div>
            <div class="queue-meta">
              ${statusBadge(isActive ? "active" : "down")}
              ${isCoordinator ? '<span class="badge violet">coordenador</span>' : ""}
              ${isLocal ? '<span class="badge">local</span>' : ""}
              <span>visto ${fmtTime(peer.last_seen)}</span>
            </div>
            <a class="mono" href="${brokerExternalUrl(id)}">${brokerExternalUrl(id)}</a>
          </article>
        `;
      }).join("");
    }

    function renderOccurrences(items) {
      const sorted = [...items].sort((a, b) => (b.created_at || 0) - (a.created_at || 0));
      $("occurrencesTable").innerHTML = sorted.map((item) => `
        <tr>
          <td class="mono">${escapeHtml(item.occurrence_id)}</td>
          <td>${statusBadge(item.status)}</td>
          <td>${escapeHtml(item.severity)}</td>
          <td>${escapeHtml(item.lamport_ts)}</td>
          <td>broker-${escapeHtml(item.broker_id)}</td>
          <td class="mono">${escapeHtml(item.assigned_drone_id || "-")}</td>
        </tr>
      `).join("") || `<tr><td colspan="6" class="empty">Nenhuma ocorrencia registrada.</td></tr>`;
    }

    function renderQueue(items) {
      $("queueList").innerHTML = items.map((item, index) => `
        <li class="queue-item">
          <div class="queue-title">
            <strong class="mono">${index + 1}. ${escapeHtml(item.occurrence_id)}</strong>
            <span class="badge amber">prioridade ${escapeHtml(item.severity)}</span>
          </div>
          <div class="queue-meta">
            <span>Lamport ${escapeHtml(item.lamport_ts)}</span>
            <span>broker-${escapeHtml(item.broker_id)}</span>
            <span>setor ${escapeHtml(item.sector_id)}</span>
            <span>${escapeHtml(item.sensor_id)}</span>
          </div>
        </li>
      `).join("") || `<li class="empty">Fila vazia.</li>`;
    }

    function renderDrones(items) {
      const sorted = [...items].sort((a, b) => String(a.drone_id).localeCompare(String(b.drone_id)));
      $("dronesTable").innerHTML = sorted.map((item) => `
        <tr>
          <td class="mono">${escapeHtml(item.drone_id)}</td>
          <td>${statusBadge(item.status)}</td>
          <td>${item.broker_id ? `broker-${escapeHtml(item.broker_id)}` : "-"}</td>
          <td class="mono">${escapeHtml(item.assigned_occurrence_id || "-")}</td>
          <td class="mono">${escapeHtml(item.callback_url)}</td>
        </tr>
      `).join("") || `<tr><td colspan="5" class="empty">Nenhum drone registrado.</td></tr>`;
    }

    function renderEvents(items) {
      $("eventsList").innerHTML = items.slice().reverse().map((item) => `
        <li class="event-item">
          <div class="event-title">
            <strong>${escapeHtml(item.component)}</strong>
            <span class="badge">${fmtTime(item.ts)}</span>
          </div>
          <div>${escapeHtml(item.message)}</div>
        </li>
      `).join("") || `<li class="empty">Nenhum evento registrado neste broker.</li>`;
    }

    function setConnection(status) {
      const el = $("connectionStatus");
      if (status === "online") {
        el.className = "badge green";
        el.textContent = "Online";
      } else if (status === "paused") {
        el.className = "badge amber";
        el.textContent = "Pausado";
      } else {
        el.className = "badge red";
        el.textContent = "Offline";
      }
    }

    async function loadState() {
      if (state.paused) return;
      try {
        const response = await fetch("/state", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        render(await response.json());
      } catch (error) {
        setConnection("offline");
        $("subtitle").textContent = `Falha ao consultar broker: ${error.message}`;
      }
    }

    async function createOccurrence(event) {
      event.preventDefault();
      $("formMessage").textContent = "Enviando...";
      const payload = {
        sector_id: Number($("sectorInput").value),
        severity: Number($("severityInput").value),
        sensor_id: "dashboard",
        description: $("descriptionInput").value || "ocorrencia manual pelo dashboard"
      };

      try {
        const response = await fetch("/occurrences", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        $("formMessage").textContent = `Criada ${data.occurrence_id}`;
        await loadState();
      } catch (error) {
        $("formMessage").textContent = `Erro: ${error.message}`;
      }
    }

    $("refreshButton").addEventListener("click", loadState);
    $("pauseButton").addEventListener("click", () => {
      state.paused = !state.paused;
      $("pauseButton").textContent = state.paused ? "Retomar" : "Pausar";
      setConnection(state.paused ? "paused" : "online");
      if (!state.paused) loadState();
    });
    $("occurrenceForm").addEventListener("submit", createOccurrence);

    loadState();
    state.timer = setInterval(loadState, 1500);
  </script>
</body>
</html>
"""
