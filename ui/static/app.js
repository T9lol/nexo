const $ = (id) => document.getElementById(id);

const money = (value) => new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
}).format(value);

const signedMoney = (value) => `${value >= 0 ? "+" : ""}${money(value)}`;

// Subtle flash when a live value changes (CSS disables it under reduced motion).
function flash(el) {
  if (!el) return;
  el.classList.remove("flash");
  void el.offsetWidth; // force reflow to restart the animation
  el.classList.add("flash");
}

function setValue(el, text) {
  if (!el) return;
  if (el.textContent && el.textContent !== text) flash(el);
  el.textContent = text;
}

function updateConnection(status, label) {
  const node = $("connection");
  node.className = `connection ${status}`;
  node.querySelector("span:last-child").textContent = label;
}

const MODE_LABELS = {
  "UI-4 runtime": { chip: "UI-4 · RUNTIME", footer: "Runtime provider · live NeXo engine" },
  "UI-3 runtime": { chip: "UI-3 · RUNTIME", footer: "Runtime provider · live NeXo engine" },
  "UI-2 runtime": { chip: "UI-2 · RUNTIME", footer: "Runtime provider · live NeXo engine" },
  "UI-1 simulation": { chip: "UI-1 · SIMULATION", footer: "Mock provider · deterministic demo" },
  "backtest review": { chip: "BACKTEST · REVIEW", footer: "Deterministic historical replay (isolated)" },
};

function updateMode(state) {
  const label = MODE_LABELS[state.mode] || {
    chip: String(state.mode || "").toUpperCase(),
    footer: String(state.mode || ""),
  };
  $("mode-chip").textContent = label.chip;
  $("footer-mode").textContent = label.footer;
}

function updateMetrics(state) {
  const { portfolio, market, selected_strategy: selected } = state;
  setValue($("equity"), money(portfolio.equity));
  setValue($("price"), money(market.price));
  $("position").textContent = `${portfolio.asset.toFixed(2)} ${market.symbol}`;
  $("position-value").textContent = `${money(portfolio.asset * market.price)} EXPOSURE`;
  $("active-strategy").textContent = selected;
  $("active-label").textContent = `Strategy ${selected}`;

  const routing = $("routing-note");
  if (routing) {
    const manual = state.control && state.control.manual_override;
    routing.innerHTML = manual
      ? `<span class="tiny-dot amber"></span> MANUAL OVERRIDE`
      : `<span class="tiny-dot"></span> ADAPTIVE ROUTING`;
  }

  const pnl = $("pnl");
  pnl.textContent = `${signedMoney(portfolio.pnl)} all time`;
  pnl.className = `metric-delta ${portfolio.pnl > 0 ? "positive" : portfolio.pnl < 0 ? "negative" : "neutral"}`;

  const btcValue = portfolio.asset * market.price;
  const allocation = portfolio.equity ? (btcValue / portfolio.equity) * 100 : 0;
  const degrees = Math.max(0, Math.min(360, allocation * 3.6));
  $("allocation-ring").style.background = `conic-gradient(var(--green) ${degrees}deg, rgba(255,255,255,.07) ${degrees}deg)`;
  $("allocation-percent").textContent = `${allocation.toFixed(0)}%`;
  $("btc-value").textContent = money(btcValue);
  $("cash-value").textContent = money(portfolio.cash);
  $("cash-row").textContent = money(portfolio.cash);
  $("units-held").textContent = portfolio.asset.toFixed(4);
  $("last-update").textContent = `UPDATED ${new Date(state.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
}

function updateTrades(trades) {
  $("trade-count").textContent = `${trades.length} ${trades.length === 1 ? "FILL" : "FILLS"}`;
  const list = $("trade-list");
  if (!trades.length) return;
  list.innerHTML = trades.slice(0, 8).map((trade) => `
    <div class="trade-row" data-trade-id="${trade.id}">
      <span class="muted">${new Date(trade.time).toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>
      <span><b class="side ${trade.action.toLowerCase()}">${trade.action}</b></span>
      <span class="strategy-tag">Strategy ${trade.strategy}</span>
      <span>${trade.amount.toFixed(2)} ${trade.symbol}</span>
      <span>${money(trade.price)}</span>
    </div>
  `).join("");
}

// Adaptive score is the selection metric the runtime evaluator exposes; fall
// back to reward x weight for older payloads that omit it.
const adaptiveOf = (item) =>
  typeof item.adaptive === "number" ? item.adaptive : item.score * item.weight;

function updateStrategies(strategies, selected) {
  const entries = Object.entries(strategies);
  const maxScore = Math.max(...entries.map(([, item]) => Math.abs(adaptiveOf(item))), 1);
  $("strategy-list").innerHTML = entries.map(([name, item]) => {
    const adaptive = adaptiveOf(item);
    const width = Math.max(4, (Math.abs(adaptive) / maxScore) * 100);
    const active = name === selected;
    return `
      <div class="strategy-card ${active ? "active" : ""}">
        <div class="strategy-card-head">
          <span class="strategy-avatar">${name}</span>
          <span class="strategy-name"><strong>Strategy ${name}</strong><span>${active ? "Receiving market events" : "Candidate model"}</span></span>
          <span class="active-badge">${active ? "● ACTIVE" : "STANDBY"}</span>
        </div>
        <div class="score-line"><span style="width:${width}%"></span></div>
        <div class="strategy-stats">
          <div><span>REWARD</span><strong>${item.score >= 0 ? "+" : ""}${item.score.toFixed(2)}</strong></div>
          <div><span>WEIGHT</span><strong>${item.weight.toFixed(4)}</strong></div>
          <div><span>ADAPTIVE</span><strong>${adaptive >= 0 ? "+" : ""}${adaptive.toFixed(2)}</strong></div>
          <div><span>UPDATES</span><strong>${item.updates}</strong></div>
        </div>
      </div>`;
  }).join("");
}

// A single persistent Canvas context. We only reallocate the backing store when
// the element's pixel size actually changes, then redraw the data each poll -
// the native-Canvas equivalent of updating a chart instance in place.
const chart = { canvas: null, ctx: null, w: 0, h: 0, dpr: 1, points: [] };

function syncChartSize() {
  if (!chart.canvas) {
    chart.canvas = $("equity-chart");
    chart.ctx = chart.canvas.getContext("2d");
  }
  const rect = chart.canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const w = Math.max(1, Math.floor(rect.width));
  const h = Math.max(1, Math.floor(rect.height));
  if (w !== chart.w || h !== chart.h || dpr !== chart.dpr) {
    chart.w = w;
    chart.h = h;
    chart.dpr = dpr;
    chart.canvas.width = Math.floor(w * dpr);
    chart.canvas.height = Math.floor(h * dpr);
  }
}

function drawChart(points) {
  chart.points = points;
  $("tick-chip").textContent = `LIVE · ${points.length} ${points.length === 1 ? "TICK" : "TICKS"}`;

  const values = points.map((point) => point.value);
  if (values.length) {
    $("chart-latest").innerHTML = `LATEST <strong>${money(values[values.length - 1])}</strong>`;
    $("chart-start").innerHTML = `START <strong>${money(values[0])}</strong>`;
  }

  const empty = $("chart-empty");
  if (points.length < 2) {
    empty.style.display = "grid";
    return;
  }
  empty.style.display = "none";

  syncChartSize();
  const ctx = chart.ctx;
  const width = chart.w;
  const height = chart.h;
  ctx.setTransform(chart.dpr, 0, 0, chart.dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const pad = { top: 18, right: 14, bottom: 22, left: 14 };
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (max - min < 2) { max += 1; min -= 1; }
  const range = max - min;
  $("chart-range").innerHTML = `RANGE <strong>${money(range)}</strong>`;

  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(152, 183, 171, 0.08)";
  for (let i = 0; i < 5; i += 1) {
    const y = pad.top + ((height - pad.top - pad.bottom) / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
  }

  const coords = points.map((point, index) => ({
    x: pad.left + (index / (points.length - 1)) * (width - pad.left - pad.right),
    y: pad.top + ((max - point.value) / range) * (height - pad.top - pad.bottom),
  }));

  const gradient = ctx.createLinearGradient(0, pad.top, 0, height - pad.bottom);
  gradient.addColorStop(0, "rgba(86, 230, 166, 0.25)");
  gradient.addColorStop(1, "rgba(86, 230, 166, 0)");
  ctx.beginPath();
  ctx.moveTo(coords[0].x, height - pad.bottom);
  coords.forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.lineTo(coords[coords.length - 1].x, height - pad.bottom);
  ctx.closePath(); ctx.fillStyle = gradient; ctx.fill();

  ctx.beginPath();
  coords.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y));
  ctx.strokeStyle = "#56e6a6"; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.stroke();

  const last = coords[coords.length - 1];
  ctx.beginPath(); ctx.arc(last.x, last.y, 4, 0, Math.PI * 2); ctx.fillStyle = "#07100f"; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = "#56e6a6"; ctx.stroke();
}

// ---- UI-4 control terminal ----
let lastControl = null;
let commandPending = false;

function setPending(on) {
  commandPending = on;
  const panel = document.querySelector(".control-panel");
  if (panel) panel.classList.toggle("pending", on);
}

function showControlStatus(message, kind) {
  const node = $("control-status");
  if (!node) return;
  node.textContent = message;
  node.className = `control-status ${kind || ""}`;
  clearTimeout(showControlStatus._t);
  if (kind === "success") {
    showControlStatus._t = setTimeout(() => {
      node.textContent = "";
      node.className = "control-status";
    }, 3200);
  }
}

async function sendCommand(path, body, pendingLabel) {
  if (commandPending) return;               // prevent double submission
  setPending(true);
  showControlStatus(pendingLabel || "Sending command…", "pending");
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const err = await response.json();
        if (err && err.detail) detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
      } catch (_) { /* non-JSON error */ }
      throw new Error(detail);
    }
    renderControl(await response.json());     // immediate optimistic sync
    showControlStatus("Command applied.", "success");
  } catch (error) {
    showControlStatus(`Command failed: ${error.message}`, "error");
  } finally {
    setPending(false);
    // The next WebSocket snapshot is authoritative; only poll if streaming is
    // not currently the live transport (e.g. during fallback).
    if (connState !== "live") pollOnce();
  }
}

function renderControl(control) {
  if (!control) return;
  lastControl = control;
  const backtest = control.mode === "backtest";

  const tradingBtn = $("trading-btn");
  if (tradingBtn) {
    const on = control.trading_enabled;
    tradingBtn.textContent = on ? "Trading live · Pause" : "Paused · Resume";
    tradingBtn.classList.toggle("paused", !on);
    tradingBtn.setAttribute("aria-pressed", String(on));
    tradingBtn.disabled = backtest;
  }

  document.querySelectorAll("#strategy-seg button").forEach((btn) => {
    btn.setAttribute("aria-pressed", String(btn.dataset.policy === control.strategy_policy));
    btn.disabled = backtest;
  });

  const riskBtn = $("risk-btn");
  if (riskBtn) {
    const enabled = control.position_limit_enabled;
    riskBtn.setAttribute("aria-checked", String(enabled));
    $("risk-text").textContent = enabled ? "Enabled" : "Disabled";
    riskBtn.disabled = backtest;
  }
  $("risk-warning").hidden = control.position_limit_enabled;

  document.querySelectorAll("#mode-seg button").forEach((btn) => {
    btn.setAttribute("aria-pressed", String(btn.dataset.mode === control.mode));
  });
}

function openConfirm() {
  $("confirm-modal").hidden = false;
  $("confirm-ok").focus();
}
function closeConfirm() {
  $("confirm-modal").hidden = true;
}

function wireControls() {
  const tradingBtn = $("trading-btn");
  if (tradingBtn) tradingBtn.addEventListener("click", () => {
    if (!lastControl) return;
    const next = !lastControl.trading_enabled;
    sendCommand("/api/control/trading", { enabled: next }, next ? "Resuming trading…" : "Pausing trading…");
  });

  document.querySelectorAll("#strategy-seg button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const policy = btn.dataset.policy;
      if (lastControl && lastControl.strategy_policy === policy) return;
      sendCommand("/api/control/strategy", { policy }, `Selecting policy ${policy}…`);
    });
  });

  const riskBtn = $("risk-btn");
  if (riskBtn) riskBtn.addEventListener("click", () => {
    if (!lastControl) return;
    if (lastControl.position_limit_enabled) {
      openConfirm();                          // disabling requires confirmation
    } else {
      sendCommand("/api/control/risk", { position_limit_enabled: true }, "Enabling position-limit policy…");
    }
  });

  document.querySelectorAll("#mode-seg button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      if (lastControl && lastControl.mode === mode) return;
      sendCommand("/api/control/mode", { mode }, mode === "backtest" ? "Running backtest replay…" : "Resuming live session…");
    });
  });

  $("confirm-cancel").addEventListener("click", closeConfirm);
  $("confirm-modal").querySelector(".modal-backdrop").addEventListener("click", closeConfirm);
  $("confirm-ok").addEventListener("click", () => {
    closeConfirm();
    sendCommand("/api/control/risk", { position_limit_enabled: false }, "Disabling position-limit policy…");
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !$("confirm-modal").hidden) closeConfirm();
  });
}
wireControls();

// ---- UI-5 realtime transport (WebSocket + graceful HTTP fallback) ----
const CONN = {
  base: 700,            // reconnect backoff base (ms)
  cap: 12000,           // backoff cap (ms)
  maxWsAttempts: 5,     // attempts before falling back to polling
  fallbackPoll: 2500,   // fallback /api/state interval (ms)
  fallbackRetry: 6000,  // how often to retry WebSocket while in fallback (ms)
  staleAfter: 8000,     // ms without any message => stale
};

let latestState = null;
let lastSeq = -1;
let lastMessageAt = 0;
let connState = "connecting";
let transport = "ws";       // "ws" | "fallback"
let ws = null;
let wsAttempts = 0;
let reconnectTimer = null;
let fallbackPollTimer = null;
let fallbackRetryTimer = null;

const CONN_LABELS = {
  connecting: ["", "Connecting"],
  live: ["online", "Live"],
  reconnecting: ["warn", "Reconnecting…"],
  fallback: ["warn", "Fallback polling"],
  disconnected: ["error", "Disconnected"],
};

function isStale() {
  return lastMessageAt > 0 && Date.now() - lastMessageAt > CONN.staleAfter;
}

function setConnection(state) {
  connState = state;
  const [cls, label] = CONN_LABELS[state] || ["", state];
  if (state === "live" && isStale()) {
    updateConnection("warn", "Live · stale");
  } else {
    updateConnection(cls, label);
  }
}

function applyState(state) {
  if (!state) return;
  latestState = state;
  if (document.hidden) return;   // defer rendering while hidden; keep latest
  updateMode(state);
  renderControl(state.control);
  updateMetrics(state);
  updateTrades(state.trades);
  updateStrategies(state.strategies, state.selected_strategy);
  drawChart(state.equity_curve);
}

function wsUrl() {
  const scheme = location.protocol === "https:" ? "wss:" : "ws:";
  return `${scheme}//${location.host}/ws`;
}

function handleMessage(event) {
  let msg;
  try { msg = JSON.parse(event.data); } catch (_) { return; }
  lastMessageAt = Date.now();
  if (msg.type === "heartbeat") { setConnection("live"); return; }
  if (msg.type !== "state") return;
  if (typeof msg.sequence === "number" && msg.sequence <= lastSeq) return; // stale/out-of-order
  lastSeq = msg.sequence;
  applyState(msg.data);
  setConnection("live");
}

function clearFallback() {
  if (fallbackPollTimer) { clearInterval(fallbackPollTimer); fallbackPollTimer = null; }
  if (fallbackRetryTimer) { clearInterval(fallbackRetryTimer); fallbackRetryTimer = null; }
}

function connectWs() {
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
  try { if (ws) { ws.onclose = null; ws.close(); } } catch (_) { /* ignore */ }
  if (connState !== "fallback") {
    setConnection(wsAttempts === 0 ? "connecting" : "reconnecting");
  }
  let socket;
  try { socket = new WebSocket(wsUrl()); } catch (_) { scheduleReconnect(); return; }
  ws = socket;
  socket.onopen = () => {
    wsAttempts = 0;
    transport = "ws";
    clearFallback();
    setConnection("live");
  };
  socket.onmessage = handleMessage;
  socket.onclose = () => {
    if (ws === socket) ws = null;
    if (transport === "fallback") return;   // fallback retry loop owns reconnection
    scheduleReconnect();
  };
}

function scheduleReconnect() {
  wsAttempts += 1;
  if (wsAttempts > CONN.maxWsAttempts) { enterFallback(); return; }
  setConnection("reconnecting");
  const backoff = Math.min(CONN.cap, CONN.base * 2 ** (wsAttempts - 1));
  const jitter = Math.random() * 0.3 * backoff;   // capped exponential backoff + jitter
  reconnectTimer = setTimeout(connectWs, backoff + jitter);
}

function enterFallback() {
  transport = "fallback";
  setConnection("fallback");
  clearFallback();
  pollOnce();
  fallbackPollTimer = setInterval(pollOnce, CONN.fallbackPoll);
  // Periodically probe the WebSocket; onopen promotes us back to streaming.
  fallbackRetryTimer = setInterval(() => { if (transport === "fallback") connectWs(); }, CONN.fallbackRetry);
}

async function pollOnce() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const state = await response.json();
    lastMessageAt = Date.now();
    applyState(state);
    if (transport === "fallback") setConnection("fallback");
  } catch (_) {
    setConnection("disconnected");
  }
}

function checkStale() {
  if (connState === "live") setConnection("live");  // recompute stale suffix
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && latestState) applyState(latestState);
});

// Resize only redraws the last known data - no extra network request.
window.addEventListener("resize", () => {
  if (chart.points.length) drawChart(chart.points);
});

setInterval(checkStale, 2000);
connectWs();
