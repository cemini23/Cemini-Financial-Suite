// Configuration
const API_BASE = "http://127.0.0.1:8000/api/v1";

// --- NAVIGATION ---
function switchView(viewName, element) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');
    
    if (element) {
        element.classList.add('active');
    } else {
        document.querySelectorAll('.sidebar-item').forEach(item => {
            if (item.innerText.toLowerCase().includes(viewName.toLowerCase())) {
                item.classList.add('active');
            }
        });
    }
}

// --- 1. WEATHER ALPHA MODULE ---
async function updateWeather() {
    try {
        const res = await fetch(`${API_BASE}/weather/scan/us`);
        const data = await res.json();
        const best = data.best_opportunity;
        const dashStatus = document.getElementById('dash-weather-status');
        const dashScore = document.getElementById('dash-weather-score');
        const weatherTemp = document.getElementById('weather-temp');
        const signalBox = document.getElementById('weather-signal');

        const fallback = data.raw_results ? data.raw_results[0].analysis : null;
        
        if (best) {
            const cityNames = {"MIA": "Miami", "CHI": "Chicago", "NYC": "New York", "AUS": "Austin", "LAX": "Los Angeles", "DEN": "Denver", "PHX": "Phoenix", "LAS": "Las Vegas"};
            const cityName = cityNames[best.city] || best.city;
            if (weatherTemp) weatherTemp.innerText = cityName;
            if (signalBox) {
                let colorClass = best.signal.includes("DIAMOND") ? "text-cyan-400" : "text-green-400";
                signalBox.innerHTML = `
                    <div class="flex justify-between items-center text-left">
                        <div class="${colorClass} font-bold text-xl">${best.signal} in ${cityName}</div>
                        <div class="bg-blue-900 px-3 py-1 rounded text-xs">EV: ${best.expected_value}x</div>
                    </div>
                    <div class="text-gray-300 mt-2 text-sm text-left">${best.reason} Target Bracket: ${best.bracket}</div>
                `;
            }
            if (dashStatus) dashStatus.innerText = `${cityName}: ${best.signal}`;
            if (dashScore) dashScore.innerText = (best.edge * 100).toFixed(0) + "%";
            updateWeatherDetails(data.raw_results.find(r => r.analysis.city === best.city).analysis);
        } else if (fallback) {
            if (weatherTemp) weatherTemp.innerText = fallback.city;
            if (signalBox) signalBox.innerText = "No nationwide arbitrage found currently.";
            if (dashStatus) dashStatus.innerText = "STABLE";
            if (dashScore) dashScore.innerText = "0%";
            updateWeatherDetails(fallback);
        }
    } catch (e) { console.error("Weather Error", e); }
}

function updateWeatherDetails(analysis) {
    const sources = analysis.sources || {};
    document.getElementById('weather-temp').innerText = analysis.consensus_temp + "°";
    document.getElementById('weather-variance').innerText = "Variance: " + analysis.variance;
    document.getElementById('weather-nws').innerText = (sources.NWS || "Err") + "°";
    document.getElementById('weather-euro').innerText = (sources.ECMWF || "--") + "°";
    document.getElementById('weather-gfs').innerText = (sources.GFS || "--") + "°";
}

// --- 2. MUSK MONITOR MODULE ---
async function updateMusk() {
    try {
        const res = await fetch(`${API_BASE}/musk/predict`);
        const data = await res.json();
        if (data.prediction) {
            if(document.getElementById('musk-prediction')) document.getElementById('musk-prediction').innerText = "Forecasted Tweets: " + data.prediction.total_daily_tweets;
            if(document.getElementById('musk-status')) document.getElementById('musk-status').innerText = data.prediction.current_status;
            if(document.getElementById('musk-velocity')) document.getElementById('musk-velocity').innerText = data.prediction.velocity_per_hour + "/hr Velocity";
            if(document.getElementById('musk-volatility')) document.getElementById('musk-volatility').innerText = data.factors.news_volatility;
            const contextEl = document.getElementById('musk-context');
            if (contextEl) {
                let factors = [];
                if (data.factors.active_launches !== "None") factors.push(`🚀 ${data.factors.active_launches.join(", ")}`);
                if (data.factors.meme_triggers.length > 0) factors.push(`🔥 ${data.factors.meme_triggers.join(", ")}`);
                contextEl.innerHTML = factors.length > 0 ? factors.map(f => `<div class="mb-1">${f}</div>`).join("") : "Nominal baseline activity.";
            }
            if(document.getElementById('dash-musk-status')) document.getElementById('dash-musk-status').innerText = data.prediction.current_status;
            const velocityScore = Math.min(100, data.prediction.velocity_per_hour * 10);
            if(document.getElementById('dash-musk-score')) document.getElementById('dash-musk-score').innerText = velocityScore.toFixed(0) + "%";
        }
    } catch (e) { console.error("Musk Error", e); }
}

// --- 3. SATOSHI VISION (BTC) MODULE ---
async function updateBTC() {
    try {
        const res = await fetch(`${API_BASE}/btc/analyze`);
        const data = await res.json();
        if (data.price) {
            if(document.getElementById('btc-price')) document.getElementById('btc-price').innerText = "$" + data.price.current.toLocaleString();
            if(document.getElementById('btc-regime')) document.getElementById('btc-regime').innerText = data.sentiment + " REGIME";
            if(document.getElementById('btc-vwap')) document.getElementById('btc-vwap').innerText = "$" + data.price.current;
            if(document.getElementById('btc-adx')) document.getElementById('btc-adx').innerText = data.indicators.ADX;
            if(document.getElementById('btc-stoch')) document.getElementById('btc-stoch').innerText = data.indicators.RSI;
            if(document.getElementById('btc-confidence')) document.getElementById('btc-confidence').innerText = data.score.split('/')[0];
            if(document.getElementById('btc-signal')) document.getElementById('btc-signal').innerText = data.trade_setup.action;
            if(document.getElementById('btc-reason')) document.getElementById('btc-reason').innerText = data.logic.join(" | ");
            
            const verdictEl = document.getElementById('btc-verdict');
            if (verdictEl) {
                let color = data.trade_setup.action.includes("BUY") ? "text-green-400" : data.trade_setup.action.includes("SELL") ? "text-red-400" : "text-gray-400";
                verdictEl.innerHTML = `<div class="${color} font-black text-4xl">${data.trade_setup.action}</div><div class="text-xs text-gray-500 mt-2">${data.sentiment} Confirmation</div>`;
            }

            if(document.getElementById('dash-btc-status')) document.getElementById('dash-btc-status').innerText = data.sentiment;
            if(document.getElementById('dash-btc-score')) document.getElementById('dash-btc-score').innerText = data.score;
        }
    } catch (e) { console.error("BTC Error", e); }
}

// --- 4. SOCIAL ALPHA MODULE ---
let monitoredTraders = [];
async function loadSocialSettings() {
    try {
        const res = await fetch(`${API_BASE}/social/analyze`); 
        const data = await res.json();
        monitoredTraders = data.traders_monitored || ["ShardiB2", "BigCheds"];
        renderTags();
        renderSocialFeed(data.signals || []);
        document.getElementById('dash-social-status').innerText = data.aggregate_sentiment || "--";
        document.getElementById('dash-social-score').innerText = (data.score * 100).toFixed(0) + "%";
        if (data.budget_used !== undefined) updateBudgetUI(data.budget_used);
        if (data.score > 0.1) {
            document.getElementById('priority-title').innerText = `SOCIAL ALPHA: ${data.aggregate_sentiment}`;
            document.getElementById('priority-reason').innerText = `Convergence across ${data.traders_monitored.length} influencers.`;
            document.getElementById('priority-score').innerText = Math.abs((data.score * 100).toFixed(0));
        }
    } catch (e) { console.error("Social Error", e); }
}

function renderTags() {
    const container = document.getElementById('trader-tags');
    if (!container) return;
    container.innerHTML = "";
    monitoredTraders.forEach((handle, index) => {
        container.innerHTML += `<span class="tag">@${handle}<i class="fa-solid fa-xmark cursor-pointer hover:text-red-400" onclick="removeTrader(${index})"></i></span>`;
    });
}

function renderSocialFeed(signals) {
    const container = document.getElementById('social-feed');
    if (!container) return;
    if (signals.length === 0) {
        container.innerHTML = `<div class="text-gray-500 text-center mt-10">No recent signals found.</div>`;
        return;
    }
    container.innerHTML = signals.map(sig => {
        const color = sig.verdict === "BULLISH" ? "text-green-400" : sig.verdict === "BEARISH" ? "text-red-400" : "text-gray-400";
        return `<div class="bg-gray-800 p-4 rounded border border-gray-700 flex justify-between items-center text-left">
                <div>
                    <div class="flex items-center gap-2">
                        <div class="font-bold text-blue-400">@${sig.trader}</div>
                        <span class="text-[8px] bg-gray-700 px-1.5 py-0.5 rounded text-gray-300 uppercase font-bold">${sig.category}</span>
                    </div>
                    <div class="text-[10px] text-gray-500 italic mt-1">${sig.content}</div>
                </div>
                <div class="${color} font-bold text-xs uppercase">${sig.verdict}</div></div>`;
    }).join("");
}

function addTrader() {
    const input = document.getElementById('new-trader-input');
    const val = input.value.trim().replace('@', '');
    if(val && !monitoredTraders.includes(val)) { monitoredTraders.push(val); input.value = ""; renderTags(); }
}

function removeTrader(index) { monitoredTraders.splice(index, 1); renderTags(); }

async function saveSocialSettings() {
    const freq = document.getElementById('scan-freq').value;
    await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ traders: monitoredTraders, social_scan_frequency: parseInt(freq) })
    });
    alert("Cemini Command: Social Configuration Updated!");
}

// --- 5. GEO-PULSE MODULE ---
async function updateGeo() {
    try {
        const res = await fetch(`${API_BASE}/geo/pulse`);
        const data = await res.json();
        const container = document.getElementById('geo-feed');
        const scoreEl = document.getElementById('geo-impact-score');
        const pill = document.getElementById('geo-status-pill');

        if (scoreEl) scoreEl.innerText = data.aggregate_impact_score;
        if (pill) {
            pill.innerText = data.aggregate_impact_score > 30 ? "VOLATILE" : "STABLE";
            pill.className = data.aggregate_impact_score > 30 ? "bg-red-900/40 text-red-400 px-4 py-2 rounded-full border border-red-500/50 font-bold text-sm" : "bg-emerald-900/40 text-emerald-400 px-4 py-2 rounded-full border border-emerald-500/50 font-bold text-sm";
        }

        if (container) {
            container.innerHTML = data.signals.map(sig => `
                <div class="bg-gray-800 p-4 rounded border border-gray-700 flex justify-between items-center text-left">
                    <div>
                        <div class="flex items-center gap-2">
                            <div class="font-bold text-red-400">${sig.source}</div>
                            <span class="text-[8px] bg-gray-700 px-1.5 py-0.5 rounded text-gray-300 uppercase font-bold">${sig.category}</span>
                        </div>
                        <div class="text-[10px] text-gray-400 mt-1">${sig.content}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-xs font-bold ${sig.impact === 'HIGH' ? 'text-orange-400' : 'text-gray-400'}">${sig.impact} IMPACT</div>
                        <div class="text-[8px] uppercase text-gray-500 font-bold">${sig.verdict}</div>
                    </div>
                </div>
            `).join("");
        }
    } catch (e) { console.error("Geo Pulse Error", e); }
}

// --- 6. MARKET ROVER MODULE ---
async function updateRover() {
    try {
        const res = await fetch(`${API_BASE}/rover/scan`);
        const data = await res.json();
        const container = document.getElementById('rover-results');
        const biasEl = document.getElementById('rover-bias');
        const contextEl = document.getElementById('rover-context');

        if (biasEl) {
            biasEl.innerText = data.macro_context.bias;
            biasEl.className = data.macro_context.bias === "BULLISH" ? "text-2xl font-bold text-emerald-400" : data.macro_context.bias === "BEARISH" ? "text-2xl font-bold text-red-400" : "text-2xl font-bold text-gray-400";
        }
        if (contextEl) {
            contextEl.innerText = `Global Volatility: ${data.macro_context.volatility} | Dominant Regime: ${data.macro_context.regime}`;
        }

        if (container) {
            if (data.findings.length === 0) {
                container.innerHTML = `<div class="text-gray-500 italic text-sm">Scanning for macro confluence...</div>`;
                return;
            }
            container.innerHTML = data.findings.map(f => `
                <div class="bg-gray-800/50 p-3 rounded border border-gray-700 flex justify-between items-center">
                    <div>
                        <div class="font-bold text-xs text-blue-400">${f.ticker}</div>
                        <div class="text-[10px] text-gray-300">${f.title}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-[10px] font-bold ${f.signal.includes('BUY') ? 'text-emerald-400' : f.signal.includes('SELL') ? 'text-red-400' : 'text-gray-500'}">${f.signal}</div>
                        <div class="text-[8px] text-gray-500 uppercase">Confidence: ${(f.confidence * 100).toFixed(0)}%</div>
                    </div>
                </div>
            `).join("");
        }
    } catch (e) { console.error("Market Rover Error", e); }
}

// --- MASTER SETTINGS ---
let tradingEnabled = false;
async function toggleTrading() {
    tradingEnabled = !tradingEnabled;
    const btn = document.getElementById('master-trade-btn');
    btn.innerText = tradingEnabled ? "Bot: ACTIVE" : "Bot: Standby";
    btn.className = tradingEnabled ? "bg-red-600 px-4 py-1 rounded text-xs font-bold uppercase tracking-wider" : "bg-success px-4 py-1 rounded text-xs font-bold uppercase tracking-wider";
    await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ trading_enabled: tradingEnabled })
    });
}

async function saveMode() {
    const isPaper = document.getElementById('mode-toggle').value === "paper";
    await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ paper_mode: isPaper })
    });
    alert(`Switched to ${isPaper ? "PAPER" : "LIVE"} Mode`);
}

async function saveParams() {
    const global = document.getElementById('param-global-threshold').value;
    const social = document.getElementById('param-social-threshold').value;
    const risk = document.getElementById('param-risk-level').value;
    await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ global_min_score: parseInt(global), social_threshold: parseFloat(social), risk_level: risk })
    });
    alert("Trading Parameters Dialed In!");
}

async function loadMasterSettings() {
    try {
        const res = await fetch(`${API_BASE}/settings`);
        const data = await res.json();
        document.getElementById('mode-toggle').value = data.paper_mode ? "paper" : "live";
        tradingEnabled = data.trading_enabled;
        const btn = document.getElementById('master-trade-btn');
        btn.innerText = tradingEnabled ? "Bot: ACTIVE" : "Bot: Standby";
        btn.className = tradingEnabled ? "bg-red-600 px-4 py-1 rounded text-xs font-bold uppercase tracking-wider" : "bg-success px-4 py-1 rounded text-xs font-bold uppercase tracking-wider";
        document.getElementById('param-global-threshold').value = data.global_min_score;
        document.getElementById('param-social-threshold').value = data.social_threshold;
        document.getElementById('param-risk-level').value = data.risk_level;
        document.getElementById('scan-freq').value = data.social_scan_frequency;
    } catch(e) { console.error("Master Settings Load Fail", e); }
}

function updateBudgetUI(used) {
    const pct = (used / 100) * 100;
    const bar = document.getElementById('api-usage-bar');
    const display = document.getElementById('api-cost-display');
    const left = document.getElementById('api-left-pct');
    if (bar) bar.style.width = `${pct}%`;
    if (display) display.innerText = `$${used.toFixed(2)} used`;
    if (left) left.innerText = `${Math.floor(100 - pct)}% left`;
    if (bar) bar.className = pct > 90 ? "bg-danger h-full" : pct > 70 ? "bg-yellow-500 h-full" : "bg-green-500 h-full";
}

async function updatePortfolio() {
    try {
        const res = await fetch(`${API_BASE}/portfolio`);
        const positions = await res.json();
        const container = document.getElementById('active-positions');
        if (!container) return;

        if (positions.length === 0 || positions.error) {
            container.innerHTML = `<div class="text-gray-600 italic text-[10px]">No active positions.</div>`;
            return;
        }

        container.innerHTML = positions.map(p => `
            <div class="bg-gray-800 p-3 rounded border border-gray-700 flex justify-between items-center mb-2">
                <div>
                    <div class="font-bold text-[10px] text-blue-400">${p.ticker}</div>
                    <div class="text-[9px] text-gray-500">Side: ${p.side.toUpperCase()}</div>
                </div>
                <div class="text-right">
                    <div class="text-white font-bold text-xs">${p.position} Contracts</div>
                    <div class="text-[9px] text-green-400">Value: $${(p.market_value_cents / 100).toFixed(2)}</div>
                </div>
            </div>
        `).join("");
    } catch (e) { console.error("Portfolio Update Fail", e); }
}

// NEW FUNCTION: Fetch the Global State
async function updateSystemStatus() {
    try {
        const res = await fetch(`${API_BASE}/system/status`);
        const data = await res.json();
        
        // 1. Update "King" Card
        const king = data.highest_conviction;
        if (document.getElementById('king-module')) {
            document.getElementById('king-module').innerText = king.module;
            document.getElementById('king-score').innerText = king.score;
            document.getElementById('king-reason').innerText = king.reason;
            document.getElementById('king-signal').innerText = `STATUS: ${king.signal}`;
            
            // Color Coding
            const scoreEl = document.getElementById('king-score');
            if (king.score >= 80) scoreEl.className = "text-5xl font-bold text-green-400 block";
            else if (king.score >= 50) scoreEl.className = "text-5xl font-bold text-yellow-400 block";
            else scoreEl.className = "text-5xl font-bold text-gray-500 block";
        }

        // 2. Update Health Pill
        const hData = data.health || { kalshi: false, key: 'NONE', harvester: false };
        const pill = document.getElementById('kalshi-connection-pill');
        const dot = document.getElementById('kalshi-dot');
        const sText = document.getElementById('kalshi-status-text');
        const kText = document.getElementById('kalshi-key-text');

        // Harvester Pill
        const hPill = document.getElementById('harvester-status-pill');
        if (hPill) {
            hPill.className = hData.harvester ? "flex items-center gap-2 bg-blue-900/30 px-3 py-1 rounded-full border border-blue-500/50" : "flex items-center gap-2 bg-gray-900/30 px-3 py-1 rounded-full border border-gray-500/50 grayscale";
        }

        if (pill) {
            if (hData.kalshi) {
                pill.className = "flex items-center gap-2 bg-emerald-900/30 px-3 py-1 rounded-full border border-emerald-500/50";
                dot.className = "w-2 h-2 rounded-full bg-emerald-400 animate-pulse";
                sText.innerText = "ONLINE";
                sText.className = "text-[10px] font-bold text-emerald-400 uppercase tracking-widest";
            } else {
                pill.className = "flex items-center gap-2 bg-red-900/30 px-3 py-1 rounded-full border border-red-500/50";
                dot.className = "w-2 h-2 rounded-full bg-white";
                sText.innerText = "OFFLINE";
                sText.className = "text-[10px] font-bold text-red-400 uppercase tracking-widest";
            }
            kText.innerText = hData.key;
        }

        // 3. Update Trade Log
        const logContainer = document.getElementById('trade-log');
        if (logContainer && data.recent_trades.length > 0) {
            logContainer.innerHTML = data.recent_trades.map(t => `
                <div class="flex justify-between items-center bg-gray-800/50 p-2 rounded border-l-2 ${t.result === 'WIN' ? 'border-green-500' : 'border-gray-500'}">
                    <div>
                        <span class="block font-bold text-white">${t.module}</span>
                        <span class="text-xs text-gray-500">${t.time}</span>
                    </div>
                    <div class="text-right">
                        <span class="block font-bold ${t.action.includes('BUY') ? 'text-green-400' : 'text-red-400'}">${t.action}</span>
                        <span class="text-xs text-gray-400">${t.price}</span>
                    </div>
                </div>
            `).join('');
        }
    } catch(e) { console.error("Status Sync Error", e); }
}

async function updateLogs() {
    try {
        const res = await fetch(`${API_BASE}/logs`);
        const logs = await res.json();
        const container = document.getElementById('dashboard-logs');
        if (!container) return;
        if (logs.length === 0) {
            container.innerHTML = `<div class="text-gray-600 italic">Listening for market signals...</div>`;
            return;
        }
        container.innerHTML = logs.map(log => {
            let color = "text-gray-400";
            if (log.level === "TRADE") color = "text-blue-400 font-bold";
            if (log.level === "SUCCESS") color = "text-green-400 font-bold";
            if (log.level === "ERROR") color = "text-red-400 font-bold";
            if (log.level === "DEBUG") color = "text-gray-600";
            return `<div class="flex gap-3 border-b border-gray-800 pb-1 text-left"><span class="text-gray-600">[${log.time}]</span><span class="${color}">${log.msg}</span></div>`;
        }).join("");
    } catch (e) { console.error("Log Update Fail", e); }
}

// --- INITIALIZE ---
async function init() {
    console.log("💎 CEMINI COMMAND INITIALIZED");
    await loadMasterSettings();
    await loadSocialSettings();
    await updateWeather();
    await updateMusk();
    await updateBTC();
    await updateGeo();
    await updateRover();
    await updateLogs();
    await updatePortfolio();
    await updateSystemStatus();
    
    setInterval(updateLogs, 5000); 
    setInterval(updatePortfolio, 10000);
    setInterval(updateSystemStatus, 2000);
    setInterval(loadSocialSettings, 30000); 
    setInterval(updateBTC, 10000);
    setInterval(updateMusk, 60000);
    setInterval(updateWeather, 300000);
    setInterval(updateGeo, 30000);
    setInterval(updateRover, 60000);
}
window.onload = init;
