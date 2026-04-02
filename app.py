"""
⚡ SNIPER MODE — Swing Trading Scanner
Quality over Quantity. One Perfect Pick.

Designed for:
- Small capital ($500-$1,000)
- Concentrated positions (all-in on 1 stock)
- Higher probability (70%+ only)
- Bigger profit targets (10%+)
- Hold 1-3 weeks
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚡ Sniper Mode",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────
#  DARK MINIMAL CSS
# ──────────────────────────────────────────────────────────────────
CSS = """
<style>
    .main .block-container { max-width: 900px; padding: 1rem 2rem; }
    
    .header { 
        font-size: 2rem; font-weight: 700; color: #ffd700;
        text-align: center; margin-bottom: 0.2rem;
    }
    .subheader { 
        color: #888; font-size: 0.9rem; text-align: center; 
        margin-bottom: 1.5rem;
    }
    
    .market-box {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border-radius: 10px; padding: 1rem; margin-bottom: 1rem;
        border: 1px solid #30363d;
    }
    
    .sniper-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 3px solid #ffd700;
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 0 30px rgba(255,215,0,0.15);
    }
    
    .ticker-big { 
        font-size: 3rem; font-weight: 800; color: #fff;
        letter-spacing: 2px;
    }
    .price-big { 
        font-size: 1.5rem; color: #888; margin-left: 1rem;
    }
    
    .prob-container {
        text-align: center; padding: 1rem;
        background: #0d1117; border-radius: 12px;
        margin: 1rem 0;
    }
    .prob-number { 
        font-size: 4rem; font-weight: 800; color: #00ff88;
    }
    .prob-label { 
        font-size: 0.9rem; color: #666; text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .levels-box {
        display: flex; justify-content: space-around;
        background: #0d1117; border-radius: 10px;
        padding: 1.5rem; margin: 1rem 0;
    }
    .level-item { text-align: center; }
    .level-value { font-size: 1.5rem; font-weight: 700; }
    .level-label { font-size: 0.75rem; color: #666; text-transform: uppercase; }
    .sl-color { color: #f85149; }
    .tp-color { color: #00ff88; }
    .entry-color { color: #ffd700; }
    
    .reason-box {
        background: #1a2332; border-left: 3px solid #ffd700;
        padding: 0.8rem 1rem; margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .reason-title { color: #ffd700; font-weight: 600; }
    .reason-text { color: #aaa; font-size: 0.9rem; margin-top: 0.3rem; }
    
    .action-box {
        background: linear-gradient(135deg, #1a3d2e 0%, #0d2818 100%);
        border: 2px solid #238636;
        border-radius: 12px; padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #3d2a1a; border: 1px solid #d29922;
        border-radius: 8px; padding: 1rem; margin: 1rem 0;
        color: #ffd700;
    }
    
    .no-signal {
        text-align: center; padding: 3rem;
        color: #666; font-size: 1.1rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #ffd700 0%, #ffaa00 100%);
        color: #000; border: none; border-radius: 10px;
        font-weight: 700; padding: 0.8rem 2rem; font-size: 1.1rem;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ffaa00 0%, #ff8800 100%);
    }
</style>
"""

# ──────────────────────────────────────────────────────────────────
#  QUALITY STOCK UNIVERSE — Only the best 40 stocks
# ──────────────────────────────────────────────────────────────────
STOCK_SECTORS = {
    # Tech Giants (most liquid, predictable)
    "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "META": "Tech", "AMZN": "Tech",
    # Semiconductors (strong trends)
    "NVDA": "Semis", "AMD": "Semis", "AVGO": "Semis", "QCOM": "Semis",
    # Finance (stable, good swings)
    "JPM": "Finance", "GS": "Finance", "V": "Payments", "MA": "Payments",
    # Healthcare (defensive + growth)
    "LLY": "Health", "UNH": "Health", "JNJ": "Health", "ABBV": "Health",
    # Consumer (predictable patterns)
    "WMT": "Retail", "COST": "Retail", "HD": "Retail", "NKE": "Consumer",
    "MCD": "Consumer", "SBUX": "Consumer",
    # Energy (momentum plays)
    "XOM": "Energy", "CVX": "Energy",
    # EV & Growth (bigger swings)
    "TSLA": "EV",
    # Cloud & SaaS (growth momentum)
    "CRM": "Cloud", "ADBE": "Cloud", "NOW": "Cloud", "SNOW": "Cloud",
    # Industrial (stable trends)
    "CAT": "Industrial", "BA": "Industrial", "DE": "Industrial",
    # Media
    "DIS": "Media", "NFLX": "Media",
    # Fintech
    "SQ": "Fintech", "PYPL": "Fintech",
}

ALL_TICKERS = list(STOCK_SECTORS.keys())

# ──────────────────────────────────────────────────────────────────
#  SNIPER CONFIGURATION — Aggressive but calculated
# ──────────────────────────────────────────────────────────────────
CFG = {
    "min_win_prob"      : 70,      # Higher threshold (was 65)
    "min_profit_pct"    : 10.0,    # Bigger targets (was 6)
    "min_rr"            : 2.5,     # Better reward/risk (was 2.0)
    "sl_atr_mult"       : 1.5,     # Stop loss = 1.5x ATR
    "tp_atr_mult"       : 4.0,     # Take profit = 4x ATR (was 3.5)
    "risk_per_trade_pct": 5.0,     # Risk 5% per trade (aggressive)
    "max_position_pct"  : 90.0,    # Use up to 90% of capital
    "scan_threads"      : 8,
}

# ──────────────────────────────────────────────────────────────────
#  MARKET REGIME — Only trade in bullish/neutral markets
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_market_regime():
    """Check if SPY is bullish, neutral, or bearish."""
    try:
        spy = yf.Ticker("SPY")
        df = spy.history(period="3mo", interval="1d")
        if df.empty or len(df) < 50:
            return "NEUTRAL", 0, "Cannot fetch SPY"
        
        c = df["Close"]
        price = float(c.iloc[-1])
        
        ema20 = c.ewm(span=20).mean().iloc[-1]
        ema50 = c.ewm(span=50).mean().iloc[-1]
        
        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = float((100 - (100 / (1 + gain / loss))).iloc[-1])
        
        # 20-day change
        chg_20d = (price - c.iloc[-20]) / c.iloc[-20] * 100
        
        score = 0
        if price > ema20 > ema50: score += 40
        elif price > ema50: score += 20
        if rsi > 50: score += 20
        if chg_20d > 0: score += 20
        if chg_20d > 3: score += 20
        
        if score >= 60:
            return "BULLISH", score, "🟢 Market is BULLISH — Good to trade"
        elif score >= 30:
            return "NEUTRAL", score, "🟡 Market is NEUTRAL — Be careful"
        else:
            return "BEARISH", score, "🔴 Market is BEARISH — Wait for better conditions"
            
    except Exception:
        return "NEUTRAL", 0, "Error checking market"


# ──────────────────────────────────────────────────────────────────
#  WEEKLY TREND CHECK — Must be bullish for swing trading
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def check_weekly_trend(ticker: str):
    """Weekly trend must be bullish for swing trading."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y", interval="1wk", auto_adjust=True)
        
        if df.empty or len(df) < 20:
            return True, 0
        
        c = df["Close"]
        price = float(c.iloc[-1])
        
        ema10 = c.ewm(span=10).mean().iloc[-1]
        ema20 = c.ewm(span=20).mean().iloc[-1]
        
        # Weekly RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = float((100 - (100 / (1 + gain / loss))).iloc[-1])
        
        score = 0
        if price > ema10 > ema20: score += 50
        elif price > ema20: score += 25
        if 40 <= rsi <= 70: score += 30
        elif rsi < 75: score += 10
        
        return score >= 50, score
        
    except Exception:
        return True, 0


# ──────────────────────────────────────────────────────────────────
#  SIGNAL PERSISTENCE — Setup must be stable for days
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def check_signal_persistence(ticker: str):
    """How many days has this setup been valid?"""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1mo", interval="1d", auto_adjust=True)
        
        if df.empty or len(df) < 10:
            return 0
        
        c = df["Close"]
        ema8 = c.ewm(span=8).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        
        valid_days = 0
        for i in range(-1, -min(10, len(df)), -1):
            price = c.iloc[i]
            if price > ema8.iloc[i] > ema21.iloc[i] and price > ema50.iloc[i]:
                valid_days += 1
            else:
                break
        
        return valid_days
    except:
        return 0


# ──────────────────────────────────────────────────────────────────
#  DATA FETCHING & INDICATORS
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(ticker: str):
    """Fetch price data and compute indicators."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y", interval="1d", auto_adjust=True)
        
        if df.empty or len(df) < 100:
            return None, None
        
        df.columns = [c.lower() for c in df.columns]
        c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
        price = float(c.iloc[-1])
        
        # EMAs
        df.ta.ema(length=8, append=True)
        df.ta.ema(length=21, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        # RSI
        df.ta.rsi(length=14, append=True)
        
        # MACD
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        
        # ATR
        df.ta.atr(length=14, append=True)
        
        # ADX
        df.ta.adx(length=14, append=True)
        
        # Supertrend
        df.ta.supertrend(length=10, multiplier=3, append=True)
        
        # Volume ratio
        vol_sma20 = v.rolling(20).mean()
        vol_ratio = v / vol_sma20
        
        # Get indicator values
        ema8 = float(df["EMA_8"].iloc[-1]) if "EMA_8" in df.columns else price
        ema21 = float(df["EMA_21"].iloc[-1]) if "EMA_21" in df.columns else price
        ema50 = float(df["EMA_50"].iloc[-1]) if "EMA_50" in df.columns else price
        ema200 = float(df["EMA_200"].iloc[-1]) if "EMA_200" in df.columns else price
        
        rsi = float(df["RSI_14"].iloc[-1]) if "RSI_14" in df.columns else 50
        rsi_prev = float(df["RSI_14"].iloc[-2]) if "RSI_14" in df.columns else 50
        
        macd_hist = float(df["MACDh_12_26_9"].iloc[-1]) if "MACDh_12_26_9" in df.columns else 0
        macd_prev = float(df["MACDh_12_26_9"].iloc[-2]) if "MACDh_12_26_9" in df.columns else 0
        
        atr = float(df["ATRr_14"].iloc[-1]) if "ATRr_14" in df.columns else price * 0.02
        adx = float(df["ADX_14"].iloc[-1]) if "ADX_14" in df.columns else 20
        plus_di = float(df["DMP_14"].iloc[-1]) if "DMP_14" in df.columns else 20
        minus_di = float(df["DMN_14"].iloc[-1]) if "DMN_14" in df.columns else 20
        
        # Supertrend direction
        st_col = [col for col in df.columns if "SUPERTd" in col]
        supertrend_bull = int(df[st_col[0]].iloc[-1]) == 1 if st_col else True
        
        # Changes
        chg_5d = (c.iloc[-1] - c.iloc[-5]) / c.iloc[-5] * 100
        chg_20d = (c.iloc[-1] - c.iloc[-20]) / c.iloc[-20] * 100
        
        ind = {
            "price": price,
            "ema8": ema8, "ema21": ema21, "ema50": ema50, "ema200": ema200,
            "rsi": rsi, "rsi_prev": rsi_prev,
            "macd_hist": macd_hist, "macd_prev": macd_prev,
            "atr": atr, "atr_pct": atr / price * 100,
            "adx": adx if not np.isnan(adx) else 20,
            "plus_di": plus_di, "minus_di": minus_di,
            "vol_ratio": float(vol_ratio.iloc[-1]),
            "supertrend_bull": supertrend_bull,
            "chg_5d": float(chg_5d),
            "chg_20d": float(chg_20d),
        }
        return ind, df
    except:
        return None, None


# ──────────────────────────────────────────────────────────────────
#  WIN PROBABILITY ALGORITHM — Sniper Edition
# ──────────────────────────────────────────────────────────────────
def calculate_win_probability(ind):
    """Calculate win probability with focus on quality signals."""
    score = 0
    max_score = 150  # Higher max for more selectivity
    reasons = []
    
    # 1. TREND ALIGNMENT (35 points) — Most important
    if ind["price"] > ind["ema8"] > ind["ema21"] > ind["ema50"] > ind["ema200"]:
        score += 35
        reasons.append(("🔥 Perfect Trend", "All EMAs aligned bullish. Strongest possible setup."))
    elif ind["price"] > ind["ema8"] > ind["ema21"] > ind["ema50"]:
        score += 25
        reasons.append(("📈 Strong Trend", "Short & mid EMAs aligned. Good momentum."))
    elif ind["price"] > ind["ema21"] > ind["ema50"]:
        score += 15
        reasons.append(("📊 Uptrend", "Above key moving averages."))
    
    # 2. ADX TREND STRENGTH (20 points)
    if ind["adx"] > 30 and ind["plus_di"] > ind["minus_di"]:
        score += 20
        reasons.append(("💪 Strong Trend", f"ADX at {ind['adx']:.0f} with bullish direction."))
    elif ind["adx"] > 25:
        score += 12
    elif ind["adx"] > 20:
        score += 5
    
    # 3. RSI SWEET SPOT (20 points)
    if 45 <= ind["rsi"] <= 60 and ind["rsi"] > ind["rsi_prev"]:
        score += 20
        reasons.append(("📈 RSI Rising", f"RSI at {ind['rsi']:.0f}, rising. Momentum building."))
    elif 40 <= ind["rsi"] <= 65:
        score += 12
    elif ind["rsi"] < 70:
        score += 5
    
    # 4. MACD CONFIRMATION (15 points)
    if ind["macd_hist"] > 0 and ind["macd_hist"] > ind["macd_prev"]:
        score += 15
        reasons.append(("✅ MACD Bullish", "Histogram positive and rising."))
    elif ind["macd_hist"] > 0:
        score += 8
    
    # 5. VOLUME (15 points)
    if ind["vol_ratio"] > 1.5:
        score += 15
        reasons.append(("📊 High Volume", f"Volume {ind['vol_ratio']:.1f}x average. Institutions active."))
    elif ind["vol_ratio"] > 1.2:
        score += 10
    elif ind["vol_ratio"] > 1.0:
        score += 5
    
    # 6. SUPERTREND (15 points)
    if ind["supertrend_bull"]:
        score += 15
        reasons.append(("🟢 Supertrend Bullish", "Trend indicator confirms upward momentum."))
    
    # 7. MOMENTUM (15 points)
    if 2 < ind["chg_5d"] < 10:
        score += 15
        reasons.append(("🚀 Strong Momentum", f"Up {ind['chg_5d']:.1f}% this week. Moving well."))
    elif 0 < ind["chg_5d"] < 15:
        score += 8
    
    # 8. NOT OVERBOUGHT (15 points bonus)
    if ind["rsi"] < 65:
        score += 15
        reasons.append(("✅ Room to Run", "Not overbought yet. More upside potential."))
    
    win_prob = min(95, int(score / max_score * 100))
    return win_prob, reasons


# ──────────────────────────────────────────────────────────────────
#  POSITION SIZING — For small capital
# ──────────────────────────────────────────────────────────────────
def calc_position(ind, capital):
    """Calculate position with aggressive but calculated sizing."""
    price = ind["price"]
    atr = ind["atr"]
    
    sl = price - atr * CFG["sl_atr_mult"]
    tp = price + atr * CFG["tp_atr_mult"]
    
    sl_pct = (price - sl) / price * 100
    tp_pct = (tp - price) / price * 100
    rr = tp_pct / sl_pct if sl_pct > 0 else 0
    
    # Position sizing based on risk
    risk_amount = capital * (CFG["risk_per_trade_pct"] / 100)
    max_position = capital * (CFG["max_position_pct"] / 100)
    
    loss_per_share = price - sl
    shares_by_risk = risk_amount / loss_per_share if loss_per_share > 0 else 0
    shares_by_max = max_position / price
    
    shares = min(shares_by_risk, shares_by_max)
    cap_used = shares * price
    
    return {
        "sl": sl, "tp": tp, "sl_pct": sl_pct, "tp_pct": tp_pct, "rr": rr,
        "shares": shares, "cap_used": cap_used,
        "cap_pct": cap_used / capital * 100,
        "max_loss": shares * loss_per_share,
        "max_gain": shares * (tp - price),
    }


# ──────────────────────────────────────────────────────────────────
#  ANALYZE SINGLE TICKER — Full analysis
# ──────────────────────────────────────────────────────────────────
def analyze_ticker(ticker, capital):
    """Full analysis of a single ticker."""
    ind, df = fetch_data(ticker)
    if ind is None:
        return None
    
    # Weekly trend check
    weekly_bull, weekly_score = check_weekly_trend(ticker)
    if not weekly_bull:
        return None
    
    # Signal persistence
    days_valid = check_signal_persistence(ticker)
    if days_valid < 2:
        return None
    
    win_prob, reasons = calculate_win_probability(ind)
    pos = calc_position(ind, capital)
    
    # Sniper filters — very strict
    if win_prob < CFG["min_win_prob"]:
        return None
    if pos["tp_pct"] < CFG["min_profit_pct"]:
        return None
    if pos["rr"] < CFG["min_rr"]:
        return None
    if not (ind["ema8"] > ind["ema21"] and ind["price"] > ind["ema50"]):
        return None
    if ind["rsi"] > 72:  # Too overbought
        return None
    
    # Bonus for strong multi-timeframe
    if weekly_score >= 60:
        win_prob = min(95, win_prob + 5)
        reasons.append(("📅 Weekly Confirmed", f"Weekly trend score: {weekly_score}/100"))
    if days_valid >= 4:
        win_prob = min(95, win_prob + 3)
        reasons.append(("🔒 Stable Setup", f"Valid for {days_valid} consecutive days."))
    
    return {
        "ticker": ticker,
        "sector": STOCK_SECTORS.get(ticker, "Other"),
        "ind": ind,
        "df": df,
        "win_prob": win_prob,
        "reasons": reasons,
        "pos": pos,
        "weekly_score": weekly_score,
        "days_valid": days_valid,
    }


# ──────────────────────────────────────────────────────────────────
#  SCAN MARKET — Find THE ONE best stock
# ──────────────────────────────────────────────────────────────────
def scan_market(tickers, capital, progress_callback=None):
    """Scan all tickers and return THE SINGLE BEST pick."""
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
    
    # Sort by win probability
    results.sort(key=lambda x: x["win_prob"], reverse=True)
    
    # Return only THE BEST ONE
    return results[0] if results else None


# ──────────────────────────────────────────────────────────────────
#  CHART
# ──────────────────────────────────────────────────────────────────
def make_chart(df, ind, pos):
    """Create chart with EMAs and trade levels."""
    df2 = df.tail(60).copy()
    c = df2["close"]
    
    ema8 = c.ewm(span=8).mean()
    ema21 = c.ewm(span=21).mean()
    ema50 = c.ewm(span=50).mean()
    
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df2.index, open=df2["open"], high=df2["high"],
        low=df2["low"], close=df2["close"],
        name="Price",
        increasing_line_color="#00ff88",
        decreasing_line_color="#f85149",
    ))
    
    # EMAs
    fig.add_trace(go.Scatter(x=df2.index, y=ema8, name="EMA 8", line=dict(color="#00bfff", width=1)))
    fig.add_trace(go.Scatter(x=df2.index, y=ema21, name="EMA 21", line=dict(color="#ffa500", width=1)))
    fig.add_trace(go.Scatter(x=df2.index, y=ema50, name="EMA 50", line=dict(color="#9370db", width=1)))
    
    # SL/TP lines
    fig.add_hline(y=pos["sl"], line_dash="dash", line_color="#f85149", 
                  annotation_text=f"Stop ${pos['sl']:.2f}", annotation_position="right")
    fig.add_hline(y=pos["tp"], line_dash="dash", line_color="#00ff88",
                  annotation_text=f"Target ${pos['tp']:.2f}", annotation_position="right")
    
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", size=10),
        xaxis=dict(gridcolor="#21262d", showgrid=True),
        yaxis=dict(gridcolor="#21262d", showgrid=True, side="right"),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.1),
        height=400,
        margin=dict(l=10, r=60, t=40, b=10),
    )
    return fig


# ──────────────────────────────────────────────────────────────────
#  MAIN UI
# ──────────────────────────────────────────────────────────────────

# Session state
if "sniper_result" not in st.session_state:
    st.session_state["sniper_result"] = None
if "capital" not in st.session_state:
    st.session_state["capital"] = 1000.0

# Inject CSS
st.markdown(CSS, unsafe_allow_html=True)

# Header
st.markdown('<div class="header">🎯 SNIPER MODE</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">One Perfect Pick · Quality Over Quantity · Built for $1,000</div>', unsafe_allow_html=True)

# Market Regime
regime, regime_score, regime_msg = get_market_regime()

regime_color = "#00ff88" if regime == "BULLISH" else "#ffd700" if regime == "NEUTRAL" else "#f85149"
st.markdown(f"""
<div class="market-box" style="border-left: 4px solid {regime_color};">
    <span style="font-size: 1.1em; font-weight: bold; color: {regime_color};">{regime_msg}</span>
    <span style="color: #666; margin-left: 12px;">(SPY Score: {regime_score}/100)</span>
</div>
""", unsafe_allow_html=True)

# Warning if bearish
if regime == "BEARISH":
    st.markdown("""
    <div class="warning-box">
        ⚠️ <b>WAIT!</b> Market conditions are not favorable. 
        Consider staying in cash until SPY turns bullish.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Capital input
col1, col2 = st.columns([2, 3])
with col1:
    capital = st.number_input(
        "💰 Your Capital (USD)",
        min_value=100.0,
        max_value=100000.0,
        value=st.session_state["capital"],
        step=100.0,
        key="capital_input"
    )
    st.session_state["capital"] = capital

with col2:
    scan_btn = st.button("🎯 FIND THE BEST TRADE", type="primary", use_container_width=True)

st.markdown("---")

# Handle scan
if scan_btn:
    st.session_state["sniper_result"] = None
    
    progress = st.progress(0, text=f"Scanning {len(ALL_TICKERS)} quality stocks...")
    
    def update_progress(pct):
        progress.progress(pct, text=f"Analyzing... {int(pct*100)}%")
    
    result = scan_market(ALL_TICKERS, capital, update_progress)
    progress.empty()
    
    st.session_state["sniper_result"] = result

# Display result
result = st.session_state.get("sniper_result")

if result is not None:
    ind = result["ind"]
    pos = result["pos"]
    reasons = result["reasons"]
    
    # THE SNIPER CARD
    st.markdown(f"""
    <div class="sniper-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span class="ticker-big">{result['ticker']}</span>
                <span class="price-big">${ind['price']:.2f}</span>
                <span style="background: #ffd700; color: #000; padding: 4px 10px; border-radius: 6px; font-weight: bold; margin-left: 12px; font-size: 0.8rem;">{result['sector']}</span>
            </div>
        </div>
        
        <div class="prob-container">
            <div class="prob-number">{result['win_prob']}%</div>
            <div class="prob-label">Win Probability</div>
        </div>
        
        <div class="levels-box">
            <div class="level-item">
                <div class="level-value entry-color">${ind['price']:.2f}</div>
                <div class="level-label">Entry Price</div>
            </div>
            <div class="level-item">
                <div class="level-value sl-color">${pos['sl']:.2f}</div>
                <div class="level-label">Stop Loss (-{pos['sl_pct']:.1f}%)</div>
            </div>
            <div class="level-item">
                <div class="level-value tp-color">${pos['tp']:.2f}</div>
                <div class="level-label">Target (+{pos['tp_pct']:.1f}%)</div>
            </div>
            <div class="level-item">
                <div class="level-value" style="color: #ffd700;">1:{pos['rr']:.1f}</div>
                <div class="level-label">Reward:Risk</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ACTION BOX
    st.markdown(f"""
    <div class="action-box">
        <div style="font-size: 1.2rem; font-weight: bold; color: #00ff88; margin-bottom: 0.8rem;">📋 YOUR TRADE PLAN</div>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 1rem; color: #ccc;">
            <div><b>Buy:</b> {pos['shares']:.2f} shares</div>
            <div><b>Capital Used:</b> ${pos['cap_used']:.0f} ({pos['cap_pct']:.0f}%)</div>
            <div><b>Max Loss:</b> <span style="color:#f85149;">${pos['max_loss']:.0f}</span></div>
            <div><b>Max Gain:</b> <span style="color:#00ff88;">${pos['max_gain']:.0f}</span></div>
        </div>
        <div style="margin-top: 1rem; color: #888; font-size: 0.9rem;">
            🔒 Setup valid for {result['days_valid']} days · 📅 Weekly score: {result['weekly_score']}/100
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # WHY THIS STOCK
    with st.expander("💡 WHY THIS STOCK? — See Analysis"):
        for title, text in reasons:
            st.markdown(f"""
            <div class="reason-box">
                <div class="reason-title">{title}</div>
                <div class="reason-text">{text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Key metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("RSI", f"{ind['rsi']:.0f}")
        col2.metric("ADX", f"{ind['adx']:.0f}")
        col3.metric("Volume", f"{ind['vol_ratio']:.1f}x")
        col4.metric("5-Day", f"{ind['chg_5d']:+.1f}%")
    
    # Chart
    with st.expander("📊 VIEW CHART"):
        fig = make_chart(result["df"], ind, pos)
        st.plotly_chart(fig, use_container_width=True)
    
    # TRADING RULES REMINDER
    st.markdown("""
    <div style="background: #1a2332; border-radius: 10px; padding: 1rem; margin-top: 1rem;">
        <div style="color: #ffd700; font-weight: bold; margin-bottom: 0.5rem;">📜 TRADING RULES</div>
        <div style="color: #888; font-size: 0.9rem; line-height: 1.6;">
            1. Only enter if market is BULLISH or NEUTRAL<br>
            2. Set your stop loss IMMEDIATELY after buying<br>
            3. Hold for 1-3 weeks (don't panic sell)<br>
            4. Take profit at target OR if RSI > 75<br>
            5. If stopped out, wait 1-2 days before next trade<br>
            6. Scan once per day (after market close)
        </div>
    </div>
    """, unsafe_allow_html=True)

elif scan_btn:
    # No results found
    st.markdown("""
    <div class="no-signal">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
        <div style="font-size: 1.3rem; color: #ffd700; margin-bottom: 0.5rem;">No Perfect Setup Found</div>
        <div style="font-size: 0.95rem; color: #888;">
            The market doesn't have any stocks meeting our strict 70%+ criteria right now.<br>
            This is actually <b>good</b> — it means we're protecting your capital.<br><br>
            <b>What to do:</b> Wait. Check back tomorrow. Patience is profitable.
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Initial state
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem; color: #888;">
        <div style="font-size: 5rem; margin-bottom: 1rem;">🎯</div>
        <div style="font-size: 1.5rem; color: #ffd700; margin-bottom: 0.5rem;">Ready to Find Your Trade</div>
        <div style="font-size: 1rem; margin-bottom: 2rem;">
            Scanning {len(ALL_TICKERS)} quality stocks to find THE ONE best opportunity.
        </div>
        <div style="font-size: 0.9rem; color: #666; line-height: 1.8;">
            ✓ 70%+ Win Probability Required<br>
            ✓ 10%+ Profit Target<br>
            ✓ Weekly + Daily Trend Confirmation<br>
            ✓ Setup must be stable for 2+ days<br>
            ✓ Designed for $500-$1,000 capital
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #555; font-size: 0.8rem;">
    ⚡ Sniper Mode v1.0 · Built for focused, quality trading · Scan once per day, not hourly
</div>
""", unsafe_allow_html=True)
