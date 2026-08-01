document.addEventListener("DOMContentLoaded", () => {
    // Navigation handling
    const navItems = document.querySelectorAll(".nav-item");
    const panels = document.querySelectorAll(".tab-panel");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute("data-tab");
            
            navItems.forEach(nav => nav.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
            
            // Set header title based on active tab
            const headerTitle = document.querySelector(".page-title");
            if (targetTab === "dashboard") headerTitle.textContent = "Market Overview";
            else if (targetTab === "morning") headerTitle.textContent = "Morning Insights";
            else if (targetTab === "momentum") headerTitle.textContent = "Momentum Stocks";
            else if (targetTab === "funds") headerTitle.textContent = "Mutual Funds Leaderboard";
        });
    });

    // Initial load
    refreshDashboard();
    
    // Auto-poll every 60 seconds to keep data fresh without reloading
    setInterval(refreshDashboard, 60000);
});

async function refreshDashboard() {
    const refreshBtnIcon = document.querySelector(".btn-refresh i");
    if (refreshBtnIcon) refreshBtnIcon.classList.add("fa-spin");

    try {
        // Fetch JSON data concurrently
        const [morningRes, eveningRes, intradayRes] = await Promise.allSettled([
            fetch("./data/morning.json").then(r => r.json()),
            fetch("./data/evening.json").then(r => r.json()),
            fetch("./data/intraday.json").then(r => r.json())
        ]);

        const morningData = morningRes.status === "fulfilled" ? morningRes.value : null;
        const eveningData = eveningRes.status === "fulfilled" ? eveningRes.value : null;
        const intradayData = intradayRes.status === "fulfilled" ? intradayRes.value : null;

        // Update dashboard elements
        updateHeaderAndOverview(morningData, eveningData, intradayData);
        if (intradayData) renderIntradaySignals(intradayData);
        if (morningData) renderMorningInsights(morningData);
        if (eveningData) {
            renderMomentumStocks(eveningData);
            renderMutualFunds(eveningData);
        }

    } catch (error) {
        console.error("[ERROR] Failed to fetch or render dashboard data: ", error);
    } finally {
        if (refreshBtnIcon) {
            setTimeout(() => {
                refreshBtnIcon.classList.remove("fa-spin");
            }, 600);
        }
    }
}

function updateHeaderAndOverview(morning, evening, intraday) {
    // Update Date Label
    const dateLabel = document.getElementById("date-label");
    const activeDate = intraday?.date || morning?.date || evening?.date;
    if (dateLabel && activeDate) {
        dateLabel.textContent = `Trading Session: ${activeDate}`;
    } else if (dateLabel) {
        dateLabel.textContent = `Local Time: ${new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}`;
    }

    // Update Overview Cards
    const signalCount = document.getElementById("signal-count");
    if (signalCount) {
        signalCount.textContent = intraday?.signals?.length || 0;
    }

    const momentumCount = document.getElementById("momentum-count");
    if (momentumCount) {
        momentumCount.textContent = evening?.momentum_stocks?.length || 0;
    }

    const giftChangePct = document.getElementById("gift-change-pct");
    const giftOpenSignal = document.getElementById("gift-open-signal");
    const giftMiniVal = document.getElementById("gift-mini-val");
    if (morning?.gift_nifty) {
        const gift = morning.gift_nifty;
        const sign = gift.change_pct >= 0 ? "+" : "";
        
        if (giftChangePct) {
            giftChangePct.textContent = `${sign}${gift.change_pct.toFixed(2)}%`;
            giftChangePct.className = `stat-value ${gift.change_pct >= 0 ? "success" : "danger"}`;
        }
        if (giftOpenSignal) giftOpenSignal.textContent = gift.open_signal;
        if (giftMiniVal) {
            giftMiniVal.textContent = `${gift.price} (${sign}${gift.change_pct.toFixed(2)}%)`;
            giftMiniVal.style.color = gift.change_pct >= 0 ? "var(--clr-success)" : "var(--clr-danger)";
        }
    }

    // Update Nifty Trend
    const niftyTrendLabel = document.getElementById("nifty-trend-label");
    if (niftyTrendLabel && intraday?.nifty_trend) {
        niftyTrendLabel.textContent = intraday.nifty_trend;
    }

    // Update Sentiment Gauge
    const sentimentIndicator = document.getElementById("sentiment-indicator");
    const sentimentText = document.getElementById("sentiment-text");
    if (sentimentIndicator && sentimentText && morning?.gift_nifty) {
        const gift = morning.gift_nifty;
        if (gift.change_pct > 0.3) {
            sentimentText.textContent = "BULLISH";
            sentimentText.className = "sentiment-text bullish";
            sentimentIndicator.style.boxShadow = "0 0 25px rgba(16, 185, 129, 0.25)";
            sentimentIndicator.style.borderColor = "var(--clr-success)";
        } else if (gift.change_pct < -0.3) {
            sentimentText.textContent = "BEARISH";
            sentimentText.className = "sentiment-text bearish";
            sentimentIndicator.style.boxShadow = "0 0 25px rgba(239, 68, 68, 0.25)";
            sentimentIndicator.style.borderColor = "var(--clr-danger)";
        } else {
            sentimentText.textContent = "NEUTRAL";
            sentimentText.className = "sentiment-text";
            sentimentIndicator.style.boxShadow = "0 0 20px rgba(99, 102, 241, 0.1)";
            sentimentIndicator.style.borderColor = "var(--border-glass)";
        }
    }
}

function renderIntradaySignals(data) {
    const list = document.getElementById("signals-list");
    if (!list) return;

    if (!data.signals || data.signals.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-magnifying-glass"></i>
                <p>Scanning markets for 15-Minute Opening Range Breakouts...</p>
            </div>
        `;
        return;
    }

    list.innerHTML = data.signals.map(s => {
        // Calculate status pill style
        let pillClass = "active";
        let statusText = "ACTIVE";
        
        if (s.status === "Target 1 Hit") {
            pillClass = "target-1";
            statusText = "T1 HIT 🎯";
        } else if (s.status === "Target 2 Hit") {
            pillClass = "target-2";
            statusText = "T2 HIT 🏆";
        } else if (s.status === "Stop Loss Hit") {
            pillClass = "sl-hit";
            statusText = "SL HIT 🛡️";
        }

        // Calculate progress bar percentages
        const totalRange = s.t2 - s.sl;
        let progressWidth = 0;
        
        if (totalRange > 0) {
            progressWidth = ((s.current_price - s.sl) / totalRange) * 100;
        }
        progressWidth = Math.max(0, Math.min(100, progressWidth)); // clamp between 0% and 100%

        const entryPct = totalRange > 0 ? ((s.entry - s.sl) / totalRange) * 100 : 0;
        const t1Pct = totalRange > 0 ? ((s.t1 - s.sl) / totalRange) * 100 : 0;

        return `
            <div class="signal-card">
                <div class="signal-card-header">
                    <div class="stock-info">
                        <div class="stock-symbol">
                            ${s.symbol}
                            <span class="status-pill ${pillClass}">${statusText}</span>
                        </div>
                        <span class="stock-company">${s.company}</span>
                    </div>
                    <span class="signal-time-badge"><i class="fa-regular fa-clock"></i> ${s.trigger_time}</span>
                </div>

                <div class="signal-values-grid">
                    <div class="val-box">
                        <span class="val-lbl">Entry Trigger</span>
                        <span class="val-num">₹${s.entry.toFixed(2)}</span>
                    </div>
                    <div class="val-box">
                        <span class="val-lbl">Stop Loss (SL)</span>
                        <span class="val-num danger">₹${s.sl.toFixed(2)}</span>
                    </div>
                    <div class="val-box">
                        <span class="val-lbl">Target 1 (1:1)</span>
                        <span class="val-num success">₹${s.t1.toFixed(2)}</span>
                    </div>
                    <div class="val-box">
                        <span class="val-lbl">Target 2 (1:2)</span>
                        <span class="val-num success">₹${s.t2.toFixed(2)}</span>
                    </div>
                </div>

                <!-- Visual progress bar -->
                <div class="progress-bar-wrapper">
                    <div class="progress-header">
                        <span>Trade Setup Progress (LTP: ₹${s.current_price.toFixed(2)})</span>
                        <span style="color: ${s.current_price >= s.entry ? "var(--clr-success)" : "var(--clr-danger)"}">
                            ${s.current_price >= s.entry ? "+" : ""}${(((s.current_price - s.entry)/s.entry)*100).toFixed(2)}%
                        </span>
                    </div>
                    <div class="progress-track-bg">
                        <div class="progress-track-fill" style="width: ${progressWidth}%"></div>
                        
                        <!-- SL tick mark at 0% -->
                        <div class="tick-mark sl" style="left: 0%"></div>
                        <div class="tick-lbl sl" style="left: 0%">SL (₹${s.sl.toFixed(1)})</div>

                        <!-- Entry tick mark -->
                        <div class="tick-mark entry" style="left: ${entryPct}%"></div>
                        <div class="tick-lbl" style="left: ${entryPct}%">Entry (₹${s.entry.toFixed(1)})</div>

                        <!-- Target 1 tick mark -->
                        <div class="tick-mark t1" style="left: ${t1Pct}%"></div>
                        <div class="tick-lbl" style="left: ${t1Pct}%">T1 (₹${s.t1.toFixed(1)})</div>

                        <!-- Target 2 tick mark at 100% -->
                        <div class="tick-mark t2" style="left: 100%"></div>
                        <div class="tick-lbl t2" style="left: 100%">T2 (₹${s.t2.toFixed(1)})</div>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

function renderMorningInsights(data) {
    // 1. Pivot Levels Table
    const pivots = data.nifty_pivots;
    if (pivots) {
        document.getElementById("pivot-r2").textContent = pivots.r2 ? Math.round(pivots.r2) : "--";
        document.getElementById("pivot-r1").textContent = pivots.r1 ? Math.round(pivots.r1) : "--";
        document.getElementById("pivot-close").textContent = pivots.close ? Math.round(pivots.close) : "--";
        document.getElementById("pivot-s1").textContent = pivots.s1 ? Math.round(pivots.s1) : "--";
        document.getElementById("pivot-s2").textContent = pivots.s2 ? Math.round(pivots.s2) : "--";
    }

    // 2. Global Indices Cards
    const indicesList = document.getElementById("global-indices-list");
    if (indicesList && data.global_indices) {
        indicesList.innerHTML = data.global_indices.map(idx => {
            if (idx.price === null) return "";
            const isUp = idx.change_pct >= 0;
            const sign = isUp ? "+" : "";
            return `
                <div class="index-card">
                    <span class="index-name">${idx.name}</span>
                    <div class="index-val-row">
                        <span class="index-val">${idx.price.toLocaleString('en-IN', { maximumFractionDigits: 1 })}</span>
                        <span class="index-chg ${isUp ? "success" : "danger"}">${sign}${idx.change_pct.toFixed(2)}%</span>
                    </div>
                </div>
            `;
        }).join("");
    }

    // 3. Macro Commodities Grid
    const macroList = document.getElementById("macro-indices-list");
    if (macroList && data.macro) {
        macroList.innerHTML = data.macro.map(m => {
            if (m.price === null) return "";
            const isUp = m.change_pct >= 0;
            const sign = isUp ? "+" : "";
            
            // Format symbol prefixes or currencies
            let displayVal = m.price;
            if (m.name.includes("Crude") || m.name.includes("Gold")) {
                displayVal = `$${m.price.toFixed(2)}`;
            } else if (m.name.includes("Yield")) {
                displayVal = `${m.price.toFixed(2)}%`;
            } else {
                displayVal = m.price.toFixed(2);
            }

            return `
                <div class="index-card">
                    <span class="index-name">${m.name}</span>
                    <div class="index-val-row">
                        <span class="index-val">${displayVal}</span>
                        <span class="index-chg ${isUp ? "success" : "danger"}">${sign}${m.change_pct.toFixed(2)}%</span>
                    </div>
                </div>
            `;
        }).join("");
    }

    // 4. Pre-market insights bullets list
    const insightsList = document.getElementById("insights-list-ul");
    if (insightsList && data.insights) {
        if (data.insights.length === 0) {
            insightsList.innerHTML = `<li><i class="fa-solid fa-circle-info"></i> Global market cues are flat/neutral. No strong directional catalysts.</li>`;
        } else {
            insightsList.innerHTML = data.insights.map(ins => {
                // Remove Markdown bold markers if any
                const cleanText = ins.replace(/\*\*/g, "");
                return `<li><i class="fa-solid fa-circle-check" style="color: var(--clr-success)"></i> ${cleanText}</li>`;
            }).join("");
        }
    }
}

function renderMomentumStocks(data) {
    const list = document.getElementById("momentum-stocks-list");
    if (!list) return;

    if (!data.momentum_stocks || data.momentum_stocks.length === 0) {
        list.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: var(--text-muted);">
                    No momentum stocks found passing swing screening criteria.
                </td>
            </tr>
        `;
        return;
    }

    list.innerHTML = data.momentum_stocks.map(s => {
        return `
            <tr>
                <td class="stock-ticker">NSE:${s.symbol}</td>
                <td>₹${s.close.toFixed(2)}</td>
                <td>₹${s.turnover.toFixed(1)} Cr</td>
                <td><span style="color: var(--clr-success); font-weight: 600;">${s.vol_expansion.toFixed(1)}x</span></td>
                <td>${s.rsi ? s.rsi.toFixed(1) : "N/A"}</td>
                <td style="font-size: 0.8rem; line-height: 1.4; color: var(--text-secondary); max-width: 320px;">${s.why}</td>
            </tr>
        `;
    }).join("");
}

function renderMutualFunds(data) {
    const container = document.getElementById("funds-categories-container");
    if (!container) return;

    if (!data.mutual_funds || Object.keys(data.mutual_funds).length === 0) {
        container.innerHTML = `
            <div class="glass-card panel-card" style="grid-column: 1 / -1; text-align: center;">
                <p style="color: var(--text-muted);">No mutual fund compounding data available.</p>
            </div>
        `;
        return;
    }

    const categories = Object.keys(data.mutual_funds);
    container.innerHTML = categories.map(cat => {
        const funds = data.mutual_funds[cat];
        
        // Emojis for categories
        let iconClass = "fa-chart-pie-simple";
        if (cat.toLowerCase().includes("large")) iconClass = "fa-scale-balanced";
        else if (cat.toLowerCase().includes("mid")) iconClass = "fa-chart-line";
        else if (cat.toLowerCase().includes("small")) iconClass = "fa-rocket";

        return `
            <div class="glass-card fund-list-card">
                <h3 class="fund-category-title">
                    <i class="fa-solid ${iconClass}" style="color: var(--clr-primary)"></i> ${cat} Funds
                </h3>
                
                <div class="fund-list">
                    ${funds.map((f, idx) => {
                        const r_1y = f.cagr_1y !== null ? `${f.cagr_1y}%` : "N/A";
                        const r_3y = f.cagr_3y !== null ? `${f.cagr_3y}%` : "N/A";
                        const r_5y = f.cagr_5y !== null ? `${f.cagr_5y}%` : "N/A";
                        const r_10y = f.cagr_10y !== null ? `${f.cagr_10y}%` : "N/A";

                        return `
                            <div class="fund-item">
                                <div class="fund-item-name">${idx + 1}. ${f.name}</div>
                                <div class="fund-cagr-row">
                                    <span>1Y: <strong>${r_1y}</strong></span>
                                    <span>3Y: <strong>${r_3y}</strong></span>
                                    <span>5Y: <strong>${r_5y}</strong></span>
                                    <span>10Y: <strong>${r_10y}</strong></span>
                                </div>
                                <div class="fund-rationale">${f.why}</div>
                            </div>
                        `;
                    }).join("")}
                </div>
            </div>
        `;
    }).join("");
}
