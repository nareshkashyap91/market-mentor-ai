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
            else if (targetTab === "options") headerTitle.textContent = "Options & Market Pulse";
            else if (targetTab === "ai-quant") headerTitle.textContent = "AI Quant Strategy";
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
        const [morningRes, eveningRes, intradayRes, optionsRes, mfRes, quantRes] = await Promise.allSettled([
            fetch("./data/morning.json").then(r => r.json()),
            fetch("./data/evening.json").then(r => r.json()),
            fetch("./data/intraday.json").then(r => r.json()),
            fetch("./data/options.json").then(r => r.json()),
            fetch("./data/mutual_funds.json").then(r => r.json()),
            fetch("./data/ai_quant.json").then(r => r.json())
        ]);

        const morningData = morningRes.status === "fulfilled" ? morningRes.value : null;
        const eveningData = eveningRes.status === "fulfilled" ? eveningRes.value : null;
        const intradayData = intradayRes.status === "fulfilled" ? intradayRes.value : null;
        const optionsData = optionsRes.status === "fulfilled" ? optionsRes.value : null;
        const mfData = mfRes.status === "fulfilled" ? mfRes.value : null;
        const quantData = quantRes.status === "fulfilled" ? quantRes.value : null;

        // Update dashboard elements
        updateHeaderAndOverview(morningData, eveningData, intradayData);
        if (intradayData) renderIntradaySignals(intradayData);
        if (morningData) renderMorningInsights(morningData);
        if (optionsData) renderOptionsPage(optionsData);
        if (quantData) renderAIQuantPage(quantData);
        if (eveningData) renderMomentumStocks(eveningData);
        if (mfData) renderMutualFunds(mfData);

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
        // Build DMA badge and description
        let dmaBadge = "";
        if (s.dma20 && s.dma50 && s.dma100 && s.dma200) {
            const alignmentText = s.dma_aligned ? "🟢 BULLISH ALIGN" : "🟡 ABOVE DMAs";
            dmaBadge = `
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    <span class="status-pill ${s.dma_aligned ? 'target-1' : 'active'}" style="font-size: 0.65rem; padding: 3px 8px; width: fit-content; text-align: center;">${alignmentText}</span>
                    <span style="font-size: 0.72rem; color: var(--text-muted); line-height: 1.3;">
                        20: <strong>₹${s.dma20.toFixed(0)}</strong> | 50: <strong>₹${s.dma50.toFixed(0)}</strong><br>
                        100: <strong>₹${s.dma100.toFixed(0)}</strong> | 200: <strong>₹${s.dma200.toFixed(0)}</strong>
                    </span>
                </div>
            `;
        } else {
            dmaBadge = `<span style="color: var(--text-muted); font-size: 0.8rem;">N/A</span>`;
        }

        const carVal = s.car_1y !== undefined ? `${s.car_1y > 0 ? '+' : ''}${s.car_1y.toFixed(1)}%` : "N/A";
        const carColor = s.car_1y > 0 ? "var(--clr-success)" : "var(--clr-danger)";

        return `
            <tr>
                <td class="stock-ticker">NSE:${s.symbol}</td>
                <td>₹${s.close.toFixed(2)}</td>
                <td style="color: ${carColor}; font-weight: 600;">${carVal}</td>
                <td>₹${s.turnover.toFixed(1)} Cr</td>
                <td><span style="color: var(--clr-success); font-weight: 600;">${s.vol_expansion.toFixed(1)}x</span></td>
                <td>${s.rsi ? s.rsi.toFixed(1) : "N/A"}</td>
                <td>${dmaBadge}</td>
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

function renderOptionsPage(data) {
    if (!data) return;

    // VIX
    const vixVal = document.getElementById("opt-vix-val");
    const vixStatus = document.getElementById("opt-vix-status");
    if (vixVal && data.vix) {
        vixVal.textContent = data.vix.value ? data.vix.value.toFixed(2) : "--";
        if (vixStatus) vixStatus.textContent = data.vix.status || "Low Volatility";
    }

    // Nifty & Bank Nifty PCR
    const indices = data.indices || {};
    const nifty = indices.NIFTY || {};
    const bank = indices.BANKNIFTY || {};

    const niftyPcr = document.getElementById("opt-nifty-pcr");
    const niftySent = document.getElementById("opt-nifty-sentiment");
    if (niftyPcr && nifty.pcr !== undefined) {
        niftyPcr.textContent = nifty.pcr.toFixed(2);
        if (niftySent) niftySent.textContent = nifty.sentiment || "Neutral";
    }

    const bankPcr = document.getElementById("opt-bank-pcr");
    const bankSent = document.getElementById("opt-bank-sentiment");
    if (bankPcr && bank.pcr !== undefined) {
        bankPcr.textContent = bank.pcr.toFixed(2);
        if (bankSent) bankSent.textContent = bank.sentiment || "Neutral";
    }

    // Render Index Open Interest Tracker Cards
    const indicesContainer = document.getElementById("options-indices-container");
    if (indicesContainer) {
        const indexKeys = Object.keys(indices);
        indicesContainer.innerHTML = indexKeys.map(key => {
            const idx = indices[key];
            const isBull = idx.sentiment && idx.sentiment.includes("BULLISH");
            const isBear = idx.sentiment && idx.sentiment.includes("BEARISH");
            const sentColor = isBull ? "var(--clr-success)" : (isBear ? "var(--clr-danger)" : "var(--clr-warning)");

            return `
                <div class="index-card" style="padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="index-name" style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">${key} SPOT</span>
                        <span class="badge" style="background: rgba(255,255,255,0.03); color: ${sentColor}; border: 1px solid var(--border-glass);">${idx.sentiment}</span>
                    </div>
                    
                    <div class="signal-values-grid" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 0;">
                        <div class="val-box">
                            <span class="val-lbl">Spot Price</span>
                            <span class="val-num">₹${idx.spot ? idx.spot.toFixed(2) : "--"}</span>
                        </div>
                        <div class="val-box">
                            <span class="val-lbl">Session VWAP</span>
                            <span class="val-num">₹${idx.vwap ? idx.vwap.toFixed(2) : "--"}</span>
                        </div>
                        <div class="val-box">
                            <span class="val-lbl">OI Resistance (Call)</span>
                            <span class="val-num danger">₹${idx.max_call_oi ? idx.max_call_oi.toFixed(0) : "--"}</span>
                        </div>
                        <div class="val-box">
                            <span class="val-lbl">OI Support (Put)</span>
                            <span class="val-num success">₹${idx.max_put_oi ? idx.max_put_oi.toFixed(0) : "--"}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join("");
    }

    // Render active Options Signals Cards
    const signalsContainer = document.getElementById("options-signals-container");
    if (signalsContainer) {
        const signals = data.options_signals || [];
        if (signals.length === 0) {
            signalsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-shield-halved"></i>
                    <p>No high-probability index options setups. Market is currently rangebound.</p>
                </div>
            `;
        } else {
            signalsContainer.innerHTML = signals.map(sig => {
                const isCE = sig.type.includes("CE");
                const pillClass = isCE ? "target-1" : "sl-hit";

                return `
                    <div class="signal-card">
                        <div class="signal-card-header">
                            <div class="stock-info">
                                <div class="stock-symbol">
                                    ${sig.option_symbol}
                                    <span class="status-pill ${pillClass}">${sig.type}</span>
                                </div>
                                <span class="stock-company">${sig.index} Index Option Setup</span>
                            </div>
                            <span class="signal-time-badge">PCR: ${sig.pcr}</span>
                        </div>

                        <div class="signal-values-grid">
                            <div class="val-box">
                                <span class="val-lbl">Spot Entry</span>
                                <span class="val-num">₹${sig.spot_price.toFixed(2)}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Spot SL</span>
                                <span class="val-num danger">₹${sig.sl_spot.toFixed(2)}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Target 1</span>
                                <span class="val-num success">₹${sig.t1_spot.toFixed(2)}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Target 2</span>
                                <span class="val-num success">₹${sig.t2_spot.toFixed(2)}</span>
                            </div>
                        </div>

                        <p style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">
                            <strong style="color: var(--text-primary)">Rationale:</strong> ${sig.rationale}
                        </p>
                    </div>
                `;
            }).join("");
        }
    }
}

function renderAIQuantPage(data) {
    if (!data) return;

    // Phase 1 Data Quality, Phase 7 Virtual Portfolio & Phase 9 Model Versioning
    const dqTag = document.getElementById("quant-dq-tag");
    const dqSummary = document.getElementById("quant-dq-summary");
    if (dqTag && data.data_quality) {
        const verStr = (data.model_metadata && data.model_metadata.model_version) ? ` [${data.model_metadata.model_version}]` : "";
        dqTag.textContent = `${data.data_type || "LIVE_DATA"}${verStr}`;
        const paperBal = data.paper_portfolio ? data.paper_portfolio.formatted_balance : "₹100,000.00";
        if (dqSummary) dqSummary.textContent = `Paper Bal: ${paperBal} | ${data.data_quality.status_summary || 'Fresh Data'}`;
    }

    // Regimes, ADX, Confidence & Expected Move
    const niftyRegime = document.getElementById("quant-nifty-regime");
    const niftyPattern = document.getElementById("quant-nifty-pattern");
    if (niftyRegime && data.nifty) {
        niftyRegime.textContent = data.nifty.regime || "SIDEWAYS";
        const adxStr = data.nifty.adx ? `ADX: ${data.nifty.adx}` : "";
        const confStr = data.nifty.confidence_score ? `Conf: ${data.nifty.confidence_score}%` : "";
        const emStr = data.nifty.expected_move ? `EM: ${data.nifty.expected_move.summary_str}` : "";
        if (niftyPattern) niftyPattern.textContent = `${adxStr} | ${confStr} | ${emStr}`;
    }

    const bankRegime = document.getElementById("quant-bank-regime");
    const bankPattern = document.getElementById("quant-bank-pattern");
    if (bankRegime && data.banknifty) {
        bankRegime.textContent = data.banknifty.regime || "SIDEWAYS";
        const adxStr = data.banknifty.adx ? `ADX: ${data.banknifty.adx}` : "";
        const confStr = data.banknifty.confidence_score ? `Conf: ${data.banknifty.confidence_score}%` : "";
        const emStr = data.banknifty.expected_move ? `EM: ${data.banknifty.expected_move.summary_str}` : "";
        if (bankPattern) bankPattern.textContent = `${adxStr} | ${confStr} | ${emStr}`;
    }

    // Render Strategy Cards
    const stratsContainer = document.getElementById("quant-strategies-container");
    if (stratsContainer) {
        const niftyStrats = (data.nifty && data.nifty.strategies) || [];
        const bankStrats = (data.banknifty && data.banknifty.strategies) || [];
        const allStrats = [...niftyStrats, ...bankStrats];

        if (allStrats.length === 0) {
            stratsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-microchip"></i>
                    <p>Evaluating multi-regime options matrix...</p>
                </div>
            `;
            stratsContainer.innerHTML = allStrats.map(s => {
                const isTop = s.is_top_pick;
                const isCredit = s.type.includes("CREDIT") || s.type.includes("STRADDLE");
                const badgeClass = isCredit ? "target-1" : "badge-indigo";
                const borderStyle = isTop ? "border-left: 5px solid #FFD700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.15);" : "border-left: 4px solid var(--clr-primary);";
                const topBadgeMarkup = isTop ? `<span class="status-pill target-1" style="background: rgba(255, 215, 0, 0.2); color: #FFD700; border: 1px solid #FFD700; font-weight: 700; margin-left: 8px;">⭐ TOP PICK (#1 RECOMMENDED)</span>` : "";

                const g = s.greeks || {};
                const m = s.margin_info || {};
                const histProb = s.historical_win_probability || s.win_prob || "70%";
                const aiConf = s.ai_confidence_score || "50%";
                const rrr = s.risk_reward_ratio || "1:1.5";
                const marginStr = m.margin_formatted ? `Margin: ${m.margin_formatted}` : "";

                const greeksMarkup = g.net_delta !== undefined ? `
                    <div style="display: flex; gap: 8px; margin-top: 8px; margin-bottom: 8px; flex-wrap: wrap;">
                        <span class="status-pill target-1">Hist Prob: ${histProb}</span>
                        <span class="status-pill badge-purple">AI Conf: ${aiConf}</span>
                        <span class="status-pill badge-blue">RRR: ${rrr}</span>
                        ${marginStr ? `<span class="status-pill target-1" style="background: rgba(16, 185, 129, 0.15); color: var(--clr-success); font-weight: 600;">${marginStr}</span>` : ""}
                        <span class="status-pill badge-indigo">Δ Delta: ${g.net_delta}</span>
                        <span class="status-pill ${g.net_theta >= 0 ? 'target-1' : 'sl-hit'}">Θ Theta: ₹${g.net_theta}/day</span>
                        <span class="status-pill" style="background: rgba(255,255,255,0.08); color: var(--text-secondary);">IV: ${g.implied_volatility_pct}%</span>
                    </div>
                ` : "";

                return `
                    <div class="signal-card" style="${borderStyle}">
                        <div class="signal-card-header">
                            <div class="stock-info">
                                <div class="stock-symbol">
                                    ${s.name}
                                    ${topBadgeMarkup}
                                    <span class="status-pill ${badgeClass}">${s.type}</span>
                                </div>
                                <span class="stock-company">Legs: ${s.legs ? s.legs.join(" | ") : "Single Leg"}</span>
                            </div>
                            <span class="signal-time-badge" style="${isTop ? 'color: #FFD700; font-weight: 700;' : ''}">Win Prob: ${s.win_prob}</span>
                        </div>

                        ${greeksMarkup}

                        <div class="signal-values-grid" style="grid-template-columns: repeat(3, 1fr);">
                            <div class="val-box">
                                <span class="val-lbl">Spot Entry</span>
                                <span class="val-num">₹${s.entry_spot ? s.entry_spot.toFixed(2) : "--"}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Max Profit</span>
                                <span class="val-num success">${s.max_profit}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Max Loss</span>
                                <span class="val-num danger">${s.max_loss}</span>
                            </div>
                        </div>

                        <p style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">
                            <strong style="color: var(--text-primary)">Rationale:</strong> ${s.rationale}
                        </p>
                    </div>
                `;
            }).join("");
        }
    }

    // Render Intraday Stocks Long & Short Setups
    const stocksContainer = document.getElementById("quant-stocks-container");
    if (stocksContainer) {
        const longs = (data.intraday_stocks && data.intraday_stocks.long_setups) || [];
        const shorts = (data.intraday_stocks && data.intraday_stocks.short_setups) || [];
        const allStockSetups = [...longs, ...shorts];

        if (allStockSetups.length === 0) {
            stocksContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-arrows-up-down-left-right"></i>
                    <p>No high-volume intraday long/short stock setups detected in current session.</p>
                </div>
            `;
        } else {
            stocksContainer.innerHTML = allStockSetups.map(st => {
                const isBuy = st.action.includes("BUY");
                const badgeClass = isBuy ? "target-1" : "sl-hit";

                return `
                    <div class="signal-card">
                        <div class="signal-card-header">
                            <div class="stock-info">
                                <div class="stock-symbol">
                                    NSE:${st.symbol}
                                    <span class="status-pill ${badgeClass}">${st.action}</span>
                                </div>
                                <span class="stock-company">Chart Pattern: ${st.pattern}</span>
                            </div>
                            <span class="signal-time-badge">Vol: ${st.vol_exp}x</span>
                        </div>

                        <div class="signal-values-grid">
                            <div class="val-box">
                                <span class="val-lbl">Trigger Price</span>
                                <span class="val-num">₹${st.close.toFixed(2)}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Stop Loss</span>
                                <span class="val-num danger">₹${st.sl.toFixed(2)}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Target 1</span>
                                <span class="val-num success">₹${st.t1.toFixed(2)}</span>
                            </div>
                            <div class="val-box">
                                <span class="val-lbl">Target 2</span>
                                <span class="val-num success">₹${st.t2.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }
}
