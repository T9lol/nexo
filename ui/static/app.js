const $ = (id) => document.getElementById(id);

const money = (value) => new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
}).format(value);

const signedMoney = (value) => `${value >= 0 ? "+" : ""}${money(value)}`;

function updateConnection(status, label) {
  const node = $("connection");
  node.className = `connection ${status}`;
  node.querySelector("span:last-child").textContent = label;
}

const MODE_LABELS = {
  "UI-3 runtime": { chip: "UI-3 · RUNTIME", footer: "Runtime provider · live NeXo engine (read-only)" },
  "UI-2 runtime": { chip: "UI-2 · RUNTIME", footer: "Runtime provider · live NeXo engine (read-only)" },
  "UI-1 simulation": { chip: "UI-1 · SIMULATION", footer: "Mock provider · deterministic demo" },
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
  $("equity").textContent = money(portfolio.equity);
  $("price").textContent = money(market.price);
  $("position").textContent = `${portfolio.asset.toFixed(2)} ${market.symbol}`;
  $("position-value").textContent = `${money(portfolio.asset * market.price)} EXPOSURE`;
  $("active-strategy").textContent = selected;
  $("active-label").textContent = `Strategy ${selected}`;

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

async function refresh() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const state = await response.json();
    updateMode(state);
    updateMetrics(state);
    updateTrades(state.trades);
    updateStrategies(state.strategies, state.selected_strategy);
    drawChart(state.equity_curve);
    updateConnection("online", "System live");
  } catch (error) {
    console.error("Dashboard refresh failed", error);
    updateConnection("error", "Disconnected");
  }
}

// Resize only redraws the last known data - no extra network request.
window.addEventListener("resize", () => {
  if (chart.points.length) drawChart(chart.points);
});
refresh();
setInterval(refresh, 1000);
