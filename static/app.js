const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const historyEl = document.getElementById("history");
const clientId = localStorage.getItem("client_id") || crypto.randomUUID();
localStorage.setItem("client_id", clientId);

const chart = LightweightCharts.createChart(document.getElementById("chart"), {
  layout: { background: { color: "#0f172a" }, textColor: "#e2e8f0" },
  grid: { vertLines: { color: "#334155" }, horzLines: { color: "#334155" } },
  width: document.getElementById("chart").clientWidth,
  height: 420,
});
const candleSeries = chart.addCandlestickSeries();
const buyLine = candleSeries.createPriceLine({ price: 0, color: "#22c55e", lineWidth: 2, title: "Buy" });
const sellLine = candleSeries.createPriceLine({ price: 0, color: "#ef4444", lineWidth: 2, title: "Sell" });
const stopLine = candleSeries.createPriceLine({ price: 0, color: "#f59e0b", lineWidth: 2, title: "SL" });

async function saveKey() {
  const apiKey = document.getElementById("apiKey").value.trim();
  if (!apiKey) {
    statusEl.textContent = "Enter API key first.";
    return;
  }
  const res = await fetch("/api/configure-key", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: clientId, api_key: apiKey }),
  });
  statusEl.textContent = res.ok ? "API key saved in backend memory." : "Failed to save key.";
}

async function analyze() {
  const symbol = document.getElementById("symbol").value.trim().toUpperCase();
  const timeframe = document.getElementById("timeframe").value;
  const mode = document.getElementById("mode").value;
  if (!symbol) return;

  statusEl.textContent = "Analyzing...";
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, timeframe, mode, client_id: clientId }),
  });
  const data = await res.json();
  if (!res.ok) {
    statusEl.textContent = data.detail || "Failed to analyze";
    return;
  }

  statusEl.textContent = `Updated at ${new Date().toLocaleTimeString()}`;
  const c = data.candles.map((x) => ({
    time: Math.floor(new Date(x.timestamp).getTime() / 1000),
    open: x.open,
    high: x.high,
    low: x.low,
    close: x.close,
  }));
  candleSeries.setData(c);

  buyLine.applyOptions({ price: data.levels.best_buy_entry || data.indicators.support });
  sellLine.applyOptions({ price: data.levels.best_sell_entry || data.indicators.resistance });
  stopLine.applyOptions({ price: data.levels.stop_loss });

  resultEl.innerHTML = `
    <strong>Stock:</strong> ${data.stock}<br>
    <strong>Trend:</strong> ${data.trend}<br>
    <strong>Signal:</strong> ${data.signal}<br>
    <strong>Best Buy:</strong> ₹${data.levels.best_buy_entry ?? "-"}<br>
    <strong>Best Sell:</strong> ₹${data.levels.best_sell_entry ?? "-"}<br>
    <strong>Stop Loss:</strong> ₹${data.levels.stop_loss}<br>
    <strong>Target 1:</strong> ₹${data.levels.target_1}<br>
    <strong>Target 2:</strong> ₹${data.levels.target_2}<br>
    <strong>Risk/Reward:</strong> ${data.levels.risk_reward_ratio}<br>
    <strong>Confidence:</strong> ${data.confidence}%<br>
    <strong>Reason:</strong> ${data.reason.join(", ")}
  `;

  await loadHistory();
}

async function loadHistory() {
  const res = await fetch("/api/history?limit=10");
  if (!res.ok) return;
  const rows = await res.json();
  historyEl.innerHTML = rows
    .map((r) => `<li>${r.created_at} | ${r.symbol} ${r.timeframe} ${r.mode} | ${r.signal} (${r.confidence}%)</li>`)
    .join("");
}

document.getElementById("setKey").addEventListener("click", saveKey);
document.getElementById("analyze").addEventListener("click", analyze);

setInterval(analyze, 60000);
window.addEventListener("resize", () => chart.applyOptions({ width: document.getElementById("chart").clientWidth }));
loadHistory();
