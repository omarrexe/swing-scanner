"""
Swing Trading Scanner — Fast & Minimal
Shows only perfect swing trade setups with high profit potential.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ──────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚡ Swing Picks",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────
#  LANGUAGE SUPPORT
# ──────────────────────────────────────────────────────────────────
LANG = {
    "en": {
        "title": "⚡ SWING PICKS",
        "subtitle": "Only perfect setups · High profit potential",
        "capital": "Capital",
        "scanning": "Scanning",
        "stocks": "stocks",
        "found": "Found",
        "perfect_setups": "perfect setups",
        "no_setups": "No perfect setups found right now. Market conditions may not be ideal.",
        "scan_btn": "⚡ Scan Market",
        "profit": "Profit",
        "entry": "Entry",
        "stop": "Stop",
        "target": "Target",
        "score": "Score",
        "rr": "R:R",
        "language": "Language",
        "settings": "Settings",
        "top_picks": "TOP PICKS",
        "analysis": "Analysis",
        "trend": "Trend",
        "momentum": "Momentum",
        "volume": "Volume",
        "position": "Position",
        "show_chart": "Chart",
        "signals_passed": "signals",
        "potential_gain": "potential gain",
        "search_placeholder": "Search ticker (e.g. AAPL)",
        "analyze": "Analyze",
    },
    "ar": {
        "title": "⚡ صفقات سوينج",
        "subtitle": "فقط الفرص المثالية · أرباح عالية",
        "capital": "رأس المال",
        "scanning": "جاري المسح",
        "stocks": "سهم",
        "found": "وجدنا",
        "perfect_setups": "فرص مثالية",
        "no_setups": "لا توجد فرص مثالية حالياً. ظروف السوق قد لا تكون مناسبة.",
        "scan_btn": "⚡ مسح السوق",
        "profit": "الربح",
        "entry": "الدخول",
        "stop": "وقف الخسارة",
        "target": "الهدف",
        "score": "النتيجة",
        "rr": "المخاطرة:العائد",
        "language": "اللغة",
        "settings": "الإعدادات",
        "top_picks": "أفضل الاختيارات",
        "analysis": "التحليل",
        "trend": "الاتجاه",
        "momentum": "الزخم",
        "volume": "الحجم",
        "position": "المركز",
        "show_chart": "الرسم البياني",
        "signals_passed": "إشارات",
        "potential_gain": "ربح محتمل",
        "search_placeholder": "ابحث عن سهم (مثال: AAPL)",
        "analyze": "تحليل",
    }
}

def t(key):
    """Get translated text for current language."""
    lang = st.session_state.get("lang", "en")
    return LANG.get(lang, LANG["en"]).get(key, key)

def is_rtl():
    """Check if current language is RTL."""
    return st.session_state.get("lang", "en") == "ar"

# ──────────────────────────────────────────────────────────────────
#  MINIMAL CSS
# ──────────────────────────────────────────────────────────────────
def get_css():
    direction = "rtl" if is_rtl() else "ltr"
    text_align = "right" if is_rtl() else "left"
    return f"""
<style>
    .main .block-container {{ max-width: 1200px; padding: 1rem 2rem; }}
    body {{ direction: {direction}; }}
    .stApp {{ direction: {direction}; }}
    
    .header {{ 
        font-size: 1.8rem; font-weight: 700; color: #00ff88;
        margin-bottom: 0.2rem; text-align: {text_align};
    }}
    .subheader {{ color: #666; font-size: 0.85rem; margin-bottom: 1rem; text-align: {text_align}; }}
    
    .pick-card {{
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 1px solid #238636;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }}
    .pick-card:hover {{ border-color: #00ff88; }}
    
    .ticker {{ font-size: 1.4rem; font-weight: 700; color: #fff; }}
    .price {{ font-size: 1.1rem; color: #8b949e; margin-left: 0.5rem; }}
    .score-badge {{
        background: #238636; color: #fff;
        padding: 0.2rem 0.6rem; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600;
    }}
    .profit {{
        font-size: 1.5rem; font-weight: 700; color: #00ff88;
    }}
    .profit-label {{ font-size: 0.75rem; color: #666; }}
    
    .levels {{
        display: flex; gap: 1rem; margin-top: 0.5rem;
        font-size: 0.85rem; color: #8b949e;
    }}
    .sl {{ color: #f85149; }}
    .tp {{ color: #00ff88; }}
    
    .summary {{ 
        color: #8b949e; font-size: 0.85rem; 
        margin-top: 0.5rem; font-style: italic;
        text-align: {text_align};
    }}
    
    .stats-row {{
        display: flex; gap: 2rem; padding: 1rem 0;
        border-bottom: 1px solid #21262d;
        margin-bottom: 1rem;
    }}
    .stat {{ text-align: center; }}
    .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #00ff88; }}
    .stat-label {{ font-size: 0.75rem; color: #666; text-transform: uppercase; }}
    
    .no-picks {{
        text-align: center; padding: 3rem;
        color: #666; font-size: 1.1rem;
    }}
    
    .lang-btn {{ 
        background: transparent; border: 1px solid #333;
        color: #8b949e; padding: 0.3rem 0.8rem; border-radius: 6px;
        cursor: pointer; font-size: 0.85rem;
    }}
    .lang-btn:hover {{ border-color: #00ff88; color: #00ff88; }}
    .lang-btn.active {{ background: #238636; border-color: #238636; color: #fff; }}
    
    .stButton > button {{
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white; border: none; border-radius: 8px;
        font-weight: 600; padding: 0.6rem 1.5rem;
    }}
    .stButton > button:hover {{ background: #2ea043; }}
    
    div[data-testid="stMetricValue"] {{ font-size: 1.2rem; }}
</style>
"""

# ──────────────────────────────────────────────────────────────────
#  EXPANDED STOCK UNIVERSE — 150+ liquid stocks for swing trading
# ──────────────────────────────────────────────────────────────────
ALL_TICKERS = [
    # Tech Giants
    "AAPL","MSFT","NVDA","AMD","META","GOOGL","TSLA","AMZN","NFLX","ADBE",
    "CRM","ORCL","QCOM","AVGO","INTC","MU","PLTR","NOW","SNOW","PANW",
    "CRWD","ZS","NET","DDOG","MDB","TEAM","SHOP","SQ","PYPL","AFRM",
    # Finance
    "JPM","BAC","GS","MS","V","MA","AXP","WFC","C","BLK","SCHW","COF",
    # Growth / Momentum
    "UBER","COIN","HOOD","SOFI","RBLX","SNAP","LYFT","ABNB","DASH","ROKU",
    "TTD","PINS","ZM","DOCU","BILL","HUBS","WDAY","VEEV","OKTA","TWLO",
    # Crypto / Mining
    "MARA","RIOT","CLSK","CIFR","HUT","BTBT","BITF",
    # Healthcare / Biotech
    "LLY","PFE","ABBV","MRK","JNJ","GILD","AMGN","BIIB","REGN","VRTX",
    "MRNA","BNTX","ISRG","DXCM","ILMN","BMY","UNH","CVS","CI","HUM",
    # Energy / Materials
    "XOM","CVX","SLB","FCX","NEM","AA","MOS","CLF","X","VALE",
    "OXY","DVN","EOG","PXD","HAL","BKR",
    # Consumer / Retail
    "WMT","COST","TGT","HD","LOW","NKE","SBUX","MCD","DIS","CMCSA",
    "LULU","DECK","ONON","CROX","ETSY","W","CHWY",
    # Industrial / Aerospace
    "BA","CAT","DE","UNP","UPS","FDX","GE","RTX","LMT","NOC",
    # EV / Clean Energy
    "RIVN","LCID","NIO","XPEV","LI","ENPH","SEDG","FSLR","RUN",
    # ETFs
    "SPY","QQQ","IWM","TQQQ","SOXL","ARKK","XLF","XLE","XLK",
]

# ──────────────────────────────────────────────────────────────────
#  SETTINGS — Stricter for perfect picks only
# ──────────────────────────────────────────────────────────────────
CFG = {
    "sl_atr_mult"      : 1.5,
    "tp_atr_mult"      : 3.5,
    "min_rr"           : 2.0,
    "min_signals"      : 6,        # Only 6+ signals (was 4)
    "min_profit_pct"   : 5.0,      # Minimum 5% profit potential
    "rsi_min"          : 35,
    "rsi_max"          : 68,
    "risk_per_trade_pct": 1.5,
    "max_position_pct" : 30.0,
    "scan_threads"     : 10,       # Parallel scanning threads
    "max_results"      : 15,       # Show top N picks only
}

# ──────────────────────────────────────────────────────────────────
#  DATA & INDICATORS (optimized)
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(ticker: str):
    """Fetch and compute all indicators for a ticker."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="6mo", interval="1d", auto_adjust=True)
        news = t.news or []
        if df.empty or len(df) < 50:
            return None, None, []
        df.columns = [c.lower() for c in df.columns]

        c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
        price = float(c.iloc[-1])

        ema8  = c.ewm(span=8,  adjust=False).mean()
        ema21 = c.ewm(span=21, adjust=False).mean()
        ema50 = c.ewm(span=50, adjust=False).mean()

        d    = c.diff()
        gain = d.clip(lower=0).rolling(14).mean()
        loss = (-d.clip(upper=0)).rolling(14).mean()
        rsi  = 100 - (100 / (1 + gain / loss))

        mf     = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        macd_h = mf - mf.ewm(span=9, adjust=False).mean()

        tr   = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
        atr  = tr.rolling(14).mean()

        sma20  = c.rolling(20).mean()
        std20  = c.rolling(20).std()
        bb_pos = (c - (sma20 - 2*std20)) / (4*std20 + 1e-9)

        vwap   = (c * v).cumsum() / v.cumsum()
        vol_r  = v / v.rolling(20).mean()

        ind = {
            "price"    : price,
            "ema8"     : float(ema8.iloc[-1]),
            "ema21"    : float(ema21.iloc[-1]),
            "ema50"    : float(ema50.iloc[-1]),
            "rsi"      : float(rsi.iloc[-1]),
            "rsi_prev" : float(rsi.iloc[-2]),
            "macd_h"   : float(macd_h.iloc[-1]),
            "macd_prev": float(macd_h.iloc[-2]),
            "atr"      : float(atr.iloc[-1]),
            "atr_pct"  : float(atr.iloc[-1]) / price * 100,
            "bb_pos"   : float(bb_pos.iloc[-1]),
            "vwap"     : float(vwap.iloc[-1]),
            "vol_r"    : float(vol_r.iloc[-1]),
            "vol_now"  : float(v.iloc[-1]),
            "chg_1d"   : float((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2] * 100),
            "chg_5d"   : float((c.iloc[-1] - c.iloc[-5]) / c.iloc[-5] * 100) if len(c) >= 5 else 0,
        }
        return ind, df, news
    except Exception:
        return None, None, []


def news_score(news_list):
    """Quick news sentiment score."""
    BULL = ["beat","raised","upgrade","outperform","growth","record","profit",
            "surge","rally","deal","launch","revenue","buyback","expand","strong"]
    BEAR = ["miss","cut","downgrade","underperform","loss","weak","decline",
            "investigation","lawsuit","layoffs","warning","bankruptcy","fraud"]
    score = 0
    for n in (news_list or [])[:8]:
        title = n.get("content", {}).get("title", "") or n.get("title", "")
        if not title:
            continue
        tl = title.lower()
        score += sum(1 for w in BULL if w in tl)
        score -= sum(1 for w in BEAR if w in tl)
    return score


def run_signals(ind, ns):
    """Run 7 checks, return count of passed signals and summary."""
    passed = 0
    summary_parts = []
    
    # 1. Trend (EMA Stack)
    if ind["ema8"] > ind["ema21"] > ind["ema50"]:
        passed += 1
        summary_parts.append(t("trend") + " ✓")
    elif ind["ema8"] > ind["ema21"]:
        passed += 1
        summary_parts.append(t("trend") + " ~")
    
    # 2. RSI
    rising = ind["rsi"] > ind["rsi_prev"]
    if CFG["rsi_min"] <= ind["rsi"] <= CFG["rsi_max"] and rising:
        passed += 1
        summary_parts.append(f"RSI {ind['rsi']:.0f} ✓")
    
    # 3. MACD
    if ind["macd_h"] > 0 and ind["macd_h"] > ind["macd_prev"]:
        passed += 1
        summary_parts.append("MACD ✓")
    elif ind["macd_h"] > 0:
        passed += 1
        summary_parts.append("MACD ~")
    
    # 4. Volume
    if ind["vol_r"] >= 1.1:
        passed += 1
        summary_parts.append(f"{t('volume')} {ind['vol_r']:.1f}x ✓")
    
    # 5. Bollinger Bands
    if 0.25 <= ind["bb_pos"] <= 0.72:
        passed += 1
        summary_parts.append("BB ✓")
    
    # 6. VWAP
    if ind["price"] > ind["vwap"]:
        passed += 1
        summary_parts.append("VWAP ✓")
    
    # 7. News
    if ns > 0:
        passed += 1
        summary_parts.append("News ✓")
    
    summary = " · ".join(summary_parts[:4])  # Keep it short
    return passed, summary


def calc_position(ind, capital):
    """Calculate position sizing and levels."""
    price = ind["price"]
    atr   = ind["atr"]
    sl    = price - atr * CFG["sl_atr_mult"]
    tp    = price + atr * CFG["tp_atr_mult"]
    sl_pct = abs((sl - price) / price * 100)
    tp_pct = (tp - price) / price * 100
    rr     = tp_pct / sl_pct if sl_pct > 0 else 0

    max_loss = capital * CFG["risk_per_trade_pct"] / 100
    max_pos  = capital * CFG["max_position_pct"] / 100
    loss_ps  = price - sl
    shares   = min(max_loss / loss_ps, max_pos / price) if loss_ps > 0 else 0
    cap_used = shares * price

    return {
        "sl": sl, "tp": tp, "sl_pct": sl_pct, "tp_pct": tp_pct, "rr": rr,
        "shares": shares, "cap_used": cap_used,
        "cap_pct": cap_used / capital * 100,
        "max_loss": shares * loss_ps,
        "max_gain": shares * (tp - price),
    }


def is_perfect_pick(ind, score, pos):
    """Check if this is a perfect swing trade setup."""
    # Must pass minimum signals
    if score < CFG["min_signals"]:
        return False
    # Must have strong trend
    if not (ind["ema8"] > ind["ema21"] and ind["price"] > ind["ema50"]):
        return False
    # Must meet R:R requirement
    if pos["rr"] < CFG["min_rr"]:
        return False
    # Must have minimum profit potential
    if pos["tp_pct"] < CFG["min_profit_pct"]:
        return False
    # Volatility must be in safe range
    if not (0.5 <= ind["atr_pct"] <= 10.0):
        return False
    return True


def analyze_ticker(ticker, capital):
    """Analyze a single ticker - used for parallel scanning."""
    ind, df, news = fetch_data(ticker)
    if ind is None:
        return None
    
    ns = news_score(news)
    score, summary = run_signals(ind, ns)
    pos = calc_position(ind, capital)
    
    if not is_perfect_pick(ind, score, pos):
        return None
    
    return {
        "ticker": ticker,
        "ind": ind,
        "df": df,
        "score": score,
        "summary": summary,
        "pos": pos,
        "ns": ns,
    }

# ──────────────────────────────────────────────────────────────────
#  PARALLEL SCANNER
# ──────────────────────────────────────────────────────────────────
def scan_market_parallel(tickers, capital, progress_callback=None):
    """Scan multiple tickers in parallel, return only perfect picks."""
    results = []
    total = len(tickers)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=CFG["scan_threads"]) as executor:
        futures = {executor.submit(analyze_ticker, ticker, capital): ticker for ticker in tickers}
        
        for future in as_completed(futures):
            completed += 1
            if progress_callback:
                progress_callback(completed / total)
            
            result = future.result()
            if result is not None:
                results.append(result)
    
    # Sort by profit potential (highest first)
    results.sort(key=lambda x: x["pos"]["tp_pct"], reverse=True)
    return results[:CFG["max_results"]]


# ──────────────────────────────────────────────────────────────────
#  MINIMAL CHART
# ──────────────────────────────────────────────────────────────────
def make_mini_chart(df, pos, ticker):
    """Create a minimal chart with SL/TP lines."""
    df2 = df.tail(60).copy()
    
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df2.index, open=df2["open"], high=df2["high"],
        low=df2["low"], close=df2["close"],
        name="Price",
        increasing_line_color="#00ff88",
        decreasing_line_color="#f85149",
    ))
    
    # SL/TP lines
    fig.add_hline(y=pos["sl"], line_dash="dash", line_color="#f85149", line_width=1)
    fig.add_hline(y=pos["tp"], line_dash="dash", line_color="#00ff88", line_width=1)
    
    fig.update_layout(
        title=None,
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", size=10),
        xaxis=dict(gridcolor="#21262d", showgrid=True, showticklabels=False),
        yaxis=dict(gridcolor="#21262d", showgrid=True, side="right"),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        height=250,
        margin=dict(l=0, r=40, t=10, b=10),
    )
    return fig


# ──────────────────────────────────────────────────────────────────
#  MAIN UI
# ──────────────────────────────────────────────────────────────────

# Session state init
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None
if "capital" not in st.session_state:
    st.session_state["capital"] = 10000.0

# Inject CSS
st.markdown(get_css(), unsafe_allow_html=True)

# Header with language toggle
col_title, col_lang = st.columns([4, 1])

with col_title:
    st.markdown(f'<div class="header">{t("title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subheader">{t("subtitle")}</div>', unsafe_allow_html=True)

with col_lang:
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button("EN", key="en_btn", use_container_width=True):
            st.session_state["lang"] = "en"
            st.rerun()
    with lang_col2:
        if st.button("عربي", key="ar_btn", use_container_width=True):
            st.session_state["lang"] = "ar"
            st.rerun()

# Controls row
col_cap, col_scan, col_search = st.columns([2, 2, 3])

with col_cap:
    capital = st.number_input(
        f"💵 {t('capital')} (USD)",
        min_value=100.0,
        max_value=1_000_000.0,
        value=st.session_state["capital"],
        step=500.0,
        label_visibility="collapsed",
    )
    st.session_state["capital"] = capital

with col_scan:
    scan_btn = st.button(t("scan_btn"), type="primary", use_container_width=True)

with col_search:
    search_col, search_btn_col = st.columns([3, 1])
    with search_col:
        ticker_search = st.text_input(
            "Search",
            placeholder=t("search_placeholder"),
            label_visibility="collapsed",
        ).upper().strip()
    with search_btn_col:
        analyze_btn = st.button(t("analyze"), use_container_width=True)

st.markdown("---")

# Handle single stock analysis
if ticker_search and analyze_btn:
    with st.spinner(f"{t('scanning')} {ticker_search}..."):
        result = analyze_ticker(ticker_search, capital)
    
    if result is None:
        # Show anyway even if not perfect
        ind, df, news = fetch_data(ticker_search)
        if ind:
            ns = news_score(news)
            score, summary = run_signals(ind, ns)
            pos = calc_position(ind, capital)
            st.warning(f"⚠️ {ticker_search}: {score}/7 {t('signals_passed')} — Not a perfect setup")
            st.markdown(f"**{t('entry')}:** ${ind['price']:.2f} | **{t('stop')}:** ${pos['sl']:.2f} | **{t('target')}:** ${pos['tp']:.2f} | **{t('profit')}:** +{pos['tp_pct']:.1f}%")
        else:
            st.error(f"Could not fetch data for {ticker_search}")
    else:
        st.session_state["scan_results"] = [result]

# Handle market scan
if scan_btn:
    st.session_state["scan_results"] = None
    progress_bar = st.progress(0, text=f"{t('scanning')} {len(ALL_TICKERS)} {t('stocks')}...")
    
    def update_progress(pct):
        progress_bar.progress(pct, text=f"{t('scanning')}... {int(pct*100)}%")
    
    results = scan_market_parallel(ALL_TICKERS, capital, update_progress)
    progress_bar.empty()
    st.session_state["scan_results"] = results

# Display results
results = st.session_state.get("scan_results")

if results is not None:
    if len(results) == 0:
        st.markdown(f'<div class="no-picks">🔍 {t("no_setups")}</div>', unsafe_allow_html=True)
    else:
        # Stats row
        st.markdown(f"### 🎯 {t('found')} **{len(results)}** {t('perfect_setups')}")
        
        # Display picks
        for r in results:
            ind = r["ind"]
            pos = r["pos"]
            
            with st.container():
                st.markdown(f"""
                <div class="pick-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                        <div>
                            <span class="ticker">{r['ticker']}</span>
                            <span class="price">${ind['price']:.2f}</span>
                            <span class="score-badge">{r['score']}/7</span>
                        </div>
                        <div class="profit">+{pos['tp_pct']:.1f}%
                            <span class="profit-label">{t('potential_gain')}</span>
                        </div>
                    </div>
                    <div class="levels">
                        <span>{t('entry')}: <b>${ind['price']:.2f}</b></span>
                        <span class="sl">{t('stop')}: <b>${pos['sl']:.2f}</b> (-{pos['sl_pct']:.1f}%)</span>
                        <span class="tp">{t('target')}: <b>${pos['tp']:.2f}</b></span>
                        <span>{t('rr')}: <b>1:{pos['rr']:.1f}</b></span>
                    </div>
                    <div class="summary">"{r['summary']}"</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable chart
                with st.expander(f"📊 {t('show_chart')} — {r['ticker']}"):
                    col_chart, col_pos = st.columns([3, 1])
                    with col_chart:
                        fig = make_mini_chart(r["df"], pos, r["ticker"])
                        st.plotly_chart(fig, use_container_width=True)
                    with col_pos:
                        st.markdown(f"**{t('position')}**")
                        st.markdown(f"Shares: **{pos['shares']:.2f}**")
                        st.markdown(f"Cost: **${pos['cap_used']:.0f}**")
                        st.markdown(f"Max Loss: **${pos['max_loss']:.0f}**")
                        st.markdown(f"Max Gain: **${pos['max_gain']:.0f}**")

elif not scan_btn and not analyze_btn:
    # Initial state - show instructions
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;color:#666;">
        <div style="font-size:3rem;margin-bottom:1rem;">⚡</div>
        <div style="font-size:1.2rem;margin-bottom:0.5rem;">{t('scan_btn')}</div>
        <div style="font-size:0.9rem;">{len(ALL_TICKERS)} {t('stocks')} · 6-7/7 {t('signals_passed')} · {CFG['min_profit_pct']}%+ {t('potential_gain')}</div>
    </div>
    """, unsafe_allow_html=True)
