const DATA_URL = "data/market.json";
const $ = (id) => document.getElementById(id);

function pct(value) { return `${Math.round(Number(value || 0))}%`; }
function money(value) { return Number(value).toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }); }
function signedPercent(value) { const n = Number(value || 0); return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`; }

function render(data) {
  $("asOf").textContent = `As of ${new Date(data.generated_at).toLocaleString()}`;
  $("buyPercent").textContent = pct(data.temperature.buy);
  $("holdPercent").textContent = pct(data.temperature.hold);
  $("sellPercent").textContent = pct(data.temperature.sell);
  $("marketScore").textContent = Math.round(data.market.score);
  $("marketLabel").textContent = data.market.label;
  $("marketSummary").textContent = data.market.summary;
  $("spyPrice").textContent = money(data.market.spy.price);
  $("spyChange").textContent = signedPercent(data.market.spy.change_percent);
  $("spyChange").className = data.market.spy.change_percent >= 0 ? "positive" : "negative";
  $("qqqPrice").textContent = money(data.market.qqq.price);
  $("qqqChange").textContent = signedPercent(data.market.qqq.change_percent);
  $("qqqChange").className = data.market.qqq.change_percent >= 0 ? "positive" : "negative";
  $("vixPrice").textContent = Number(data.market.vix.price).toFixed(2);
  $("vixStatus").textContent = data.market.vix.status;
  $("trendStatus").textContent = data.market.trend;

  $("candidateRows").innerHTML = data.candidates.map(item => `
    <tr>
      <td><strong>${item.symbol}</strong></td>
      <td>${money(item.price)}</td>
      <td class="${item.change_percent >= 0 ? "positive" : "negative"}">${signedPercent(item.change_percent)}</td>
      <td><strong>${Math.round(item.score)}</strong></td>
      <td class="signal signal-${item.signal.toLowerCase()}">${item.signal}</td>
      <td>${item.reason}</td>
    </tr>`).join("");

  $("allocation").innerHTML = data.starter_plan.map(item => `
    <div class="allocation-row">
      <strong>${item.label}</strong>
      <div class="bar"><span style="width:${item.percent}%"></span></div>
      <span>${pct(item.percent)}</span>
    </div>`).join("");
}

async function loadData() {
  $("errorMessage").hidden = true;
  try {
    const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    render(await response.json());
  } catch (error) {
    $("errorMessage").hidden = false;
    $("errorMessage").textContent = `Could not load market data: ${error.message}. Run the updater or check data/market.json.`;
  }
}

$("refreshButton").addEventListener("click", loadData);
loadData();
