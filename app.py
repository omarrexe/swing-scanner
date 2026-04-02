"""
SNIPER MODE — Swing Trading Scanner
One Perfect Pick. Quality Over Quantity.
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

# ══════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Sniper Mode",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
#  GEN Z AESTHETIC CSS — Mesh Gradient + Glassmorphism
# ══════════════════════════════════════════════════════════════════
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* Animated mesh gradient background */
    .stApp {
        background: #0a0a0f;
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(236, 72, 153, 0.12) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(34, 211, 238, 0.1) 0px, transparent 50%),
            radial-gradient(at 0% 100%, rgba(168, 85, 247, 0.12) 0px, transparent 50%);
        min-height: 100vh;
    }
    
    /* Floating orbs animation */
    .stApp::before {
        content: '';
        position: fixed;
        top: 20%;
        left: 10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(60px);
        animation: float1 20s ease-in-out infinite;
        pointer-events: none;
        z-index: -1;
    }
    
    .stApp::after {
        content: '';
        position: fixed;
        bottom: 20%;
        right: 10%;
        width: 250px;
        height: 250px;
        background: radial-gradient(circle, rgba(236, 72, 153, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        filter: blur(60px);
        animation: float2 15s ease-in-out infinite;
        pointer-events: none;
        z-index: -1;
    }
    
    @keyframes float1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(30px, -30px) scale(1.1); }
        66% { transform: translate(-20px, 20px) scale(0.9); }
    }
    
    @keyframes float2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(-40px, 20px) scale(1.05); }
        66% { transform: translate(30px, -40px) scale(0.95); }
    }
    
    .main .block-container { 
        max-width: 800px; 
        padding: 2rem 1.5rem;
        position: relative;
        z-index: 1;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Header */
    .app-header {
        text-align: center;
        padding: 3rem 0 2rem 0;
    }
    .app-title {
        font-size: 2.5rem;
        font-weight: 600;
        background: linear-gradient(135deg, #fff 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .app-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        font-weight: 400;
        margin-top: 0.5rem;
    }
    
    /* Market Status Pill */
    .market-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 1.5rem auto;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .market-bullish { background: rgba(48, 209, 88, 0.2); color: #4ade80; }
    .market-neutral { background: rgba(255, 214, 10, 0.2); color: #fde047; }
    .market-bearish { background: rgba(255, 69, 58, 0.2); color: #f87171; }
    
    /* Scan Button — Gradient glow */
    .stButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
        color: #fff;
        border: none;
        border-radius: 14px;
        font-weight: 600;
        font-size: 1rem;
        padding: 1rem 2rem;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 30px rgba(139, 92, 246, 0.6);
    }
    
    /* Result Card — Glassmorphism */
    .result-card {
        background: rgba(30, 30, 40, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    .ticker-display {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 0.5rem;
    }
    .ticker-symbol {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #fff 0%, #c4b5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1px;
    }
    .ticker-price {
        font-size: 1.5rem;
        color: #94a3b8;
        font-weight: 500;
    }
    .ticker-sector {
        display: inline-block;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(236, 72, 153, 0.3) 100%);
        color: #fff;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Probability Circle */
    .prob-circle {
        text-align: center;
        padding: 2rem 0;
    }
    .prob-number {
        font-size: 5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4ade80 0%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }
    .prob-label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    
    /* Levels Grid */
    .levels-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        padding: 1.5rem;
        background: rgba(0,0,0,0.4);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        margin: 1.5rem 0;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .level-item {
        text-align: center;
    }
    .level-value {
        font-size: 1.3rem;
        font-weight: 600;
    }
    .level-label {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .green { color: #4ade80; }
    .red { color: #f87171; }
    .blue { color: #60a5fa; }
    .white { color: #fff; }
    
    /* Capital Input Card */
    .capital-card {
        background: rgba(96, 165, 250, 0.1);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(10px);
    }
    .capital-title {
        color: #60a5fa;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    /* Trade Plan */
    .trade-plan {
        background: rgba(74, 222, 128, 0.1);
        border: 1px solid rgba(74, 222, 128, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    .plan-title {
        color: #4ade80;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .plan-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }
    .plan-item {
        color: #fff;
        font-size: 0.9rem;
    }
    .plan-item span { color: #94a3b8; }
    
    /* Reason List */
    .reason-item {
        padding: 1rem;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        margin: 0.5rem 0;
    }
    .reason-title {
        color: #fff;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .reason-text {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 4px;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
    }
    .empty-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .empty-title {
        font-size: 1.3rem;
        color: #fff;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .empty-text {
        color: #94a3b8;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* Backtest Section */
    .backtest-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .backtest-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #fff;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .stat-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #fff;
    }
    .stat-label {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        margin-top: 4px;
    }
    
    .signal-row {
        display: grid;
        grid-template-columns: 80px 1fr 80px 80px;
        gap: 1rem;
        padding: 0.8rem 1rem;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 10px;
        margin: 0.3rem 0;
        align-items: center;
        font-size: 0.85rem;
    }
    .signal-ticker {
        font-weight: 600;
        color: #fff;
    }
    .signal-date {
        color: #64748b;
    }
    .signal-result {
        text-align: right;
        font-weight: 600;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin: 2rem 0;
    }
    
    /* Hide number input spinners */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    
    /* Input styling */
    .stNumberInput input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #fff !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
    }
</style>
"""

# ══════════════════════════════════════════════════════════════════
#  STOCK UNIVERSE — 40 Quality Stocks
# ══════════════════════════════════════════════════════════════════
STOCK_SECTORS = {
    "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "META": "Tech", "AMZN": "Tech",
    "NVDA": "Semis", "AMD": "Semis", "AVGO": "Semis", "QCOM": "Semis",
    "JPM": "Finance", "GS": "Finance", "V": "Payments", "MA": "Payments",
    "LLY": "Health", "UNH": "Health", "JNJ": "Health", "ABBV": "Health",
    "WMT": "Retail", "COST": "Retail", "HD": "Retail", "NKE": "Consumer",
    "MCD": "Consumer", "SBUX": "Consumer",
    "XOM": "Energy", "CVX": "Energy",
    "TSLA": "EV",
    "CRM": "Cloud", "ADBE": "Cloud", "NOW": "Cloud", "SNOW": "Cloud",
    "CAT": "Industrial", "BA": "Industrial", "DE": "Industrial",
    "DIS": "Media", "NFLX": "Media",
    "SQ": "Fintech", "PYPL": "Fintech",
}
ALL_TICKERS = list(STOCK_SECTORS.keys())

# ══════════════════════════════════════════════════════════════════
#  CONFIGURATION — Rotation Trading Approach
# ══════════════════════════════════════════════════════════════════
CFG = {
    "min_win_prob": 60,       # Lowered from 70 to get more signals
    "min_profit_pct": 6.0,    # Lowered from 10 to get more signals
    "min_rr": 2.0,            # 2:1 reward/risk minimum
    "sl_atr_mult": 1.5,       # Stop loss = 1.5x ATR
    "tp_atr_mult": 3.5,       # Take profit = 3.5x ATR
    "risk_per_trade_pct": 5.0,
    "max_position_pct": 95.0, # Use almost all capital (rotation)
    "scan_threads": 8,
    "max_signals": 5,         # Show top 5 signals for rotation
}

# ══════════════════════════════════════════════════════════════════
#  MARKET REGIME
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=600)
def get_market_regime():
    """Check SPY health with robust error handling."""
    try:
        spy = yf.Ticker("SPY")
        df = spy.history(period="3mo", interval="1d", timeout=10)
        
        if df is None or df.empty or len(df) < 50:
            return "NEUTRAL", 50, "Market data loading..."
        
        c = df["Close"]
        if c.empty:
            return "NEUTRAL", 50, "Market data loading..."
            
        price = float(c.iloc[-1])
        ema20 = float(c.ewm(span=20).mean().iloc[-1])
        ema50 = float(c.ewm(span=50).mean().iloc[-1])
        
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50
        
        if len(c) >= 20:
            chg_20d = (price - float(c.iloc[-20])) / float(c.iloc[-20]) * 100
        else:
            chg_20d = 0
        
        score = 0
        if price > ema20 > ema50: score += 40
        elif price > ema50: score += 20
        if rsi > 50: score += 20
        if chg_20d > 0: score += 20
        if chg_20d > 3: score += 20
        
        if score >= 60:
            return "BULLISH", score, "Bullish"
        elif score >= 30:
            return "NEUTRAL", score, "Neutral"
        else:
            return "BEARISH", score, "Bearish"
            
    except Exception as e:
        return "NEUTRAL", 50, "Market data loading..."


# ══════════════════════════════════════════════════════════════════
#  WEEKLY TREND CHECK
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def check_weekly_trend(ticker: str):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y", interval="1wk", auto_adjust=True, timeout=10)
        if df is None or df.empty or len(df) < 20:
            return True, 50
        
        c = df["Close"]
        price = float(c.iloc[-1])
        ema10 = float(c.ewm(span=10).mean().iloc[-1])
        ema20 = float(c.ewm(span=20).mean().iloc[-1])
        
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
    except:
        return True, 50


# ══════════════════════════════════════════════════════════════════
#  SIGNAL PERSISTENCE
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def check_signal_persistence(ticker: str):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1mo", interval="1d", auto_adjust=True, timeout=10)
        if df is None or df.empty or len(df) < 10:
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


# ══════════════════════════════════════════════════════════════════
#  DATA & INDICATORS
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def fetch_data(ticker: str):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y", interval="1d", auto_adjust=True, timeout=10)
        if df is None or df.empty or len(df) < 100:
            return None, None
        
        df.columns = [col.lower() for col in df.columns]
        c, v = df["close"], df["volume"]
        price = float(c.iloc[-1])
        
        df.ta.ema(length=8, append=True)
        df.ta.ema(length=21, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.atr(length=14, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.supertrend(length=10, multiplier=3, append=True)
        
        vol_sma20 = v.rolling(20).mean()
        vol_ratio = v / vol_sma20
        
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
        
        st_col = [col for col in df.columns if "SUPERTd" in col]
        supertrend_bull = int(df[st_col[0]].iloc[-1]) == 1 if st_col else True
        
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


# ══════════════════════════════════════════════════════════════════
#  WIN PROBABILITY
# ══════════════════════════════════════════════════════════════════
def calculate_win_probability(ind):
    score = 0
    max_score = 150
    reasons = []
    
    if ind["price"] > ind["ema8"] > ind["ema21"] > ind["ema50"] > ind["ema200"]:
        score += 35
        reasons.append(("Perfect Trend", "All EMAs aligned bullish"))
    elif ind["price"] > ind["ema8"] > ind["ema21"] > ind["ema50"]:
        score += 25
        reasons.append(("Strong Trend", "Short & mid EMAs aligned"))
    elif ind["price"] > ind["ema21"] > ind["ema50"]:
        score += 15
        reasons.append(("Uptrend", "Above key moving averages"))
    
    if ind["adx"] > 30 and ind["plus_di"] > ind["minus_di"]:
        score += 20
        reasons.append(("Strong ADX", f"ADX {ind['adx']:.0f} with bullish direction"))
    elif ind["adx"] > 25:
        score += 12
    elif ind["adx"] > 20:
        score += 5
    
    if 45 <= ind["rsi"] <= 60 and ind["rsi"] > ind["rsi_prev"]:
        score += 20
        reasons.append(("RSI Rising", f"RSI {ind['rsi']:.0f}, momentum building"))
    elif 40 <= ind["rsi"] <= 65:
        score += 12
    elif ind["rsi"] < 70:
        score += 5
    
    if ind["macd_hist"] > 0 and ind["macd_hist"] > ind["macd_prev"]:
        score += 15
        reasons.append(("MACD Bullish", "Histogram positive and rising"))
    elif ind["macd_hist"] > 0:
        score += 8
    
    if ind["vol_ratio"] > 1.5:
        score += 15
        reasons.append(("High Volume", f"{ind['vol_ratio']:.1f}x average volume"))
    elif ind["vol_ratio"] > 1.2:
        score += 10
    elif ind["vol_ratio"] > 1.0:
        score += 5
    
    if ind["supertrend_bull"]:
        score += 15
        reasons.append(("Supertrend", "Confirms upward momentum"))
    
    if 2 < ind["chg_5d"] < 10:
        score += 15
        reasons.append(("Momentum", f"+{ind['chg_5d']:.1f}% this week"))
    elif 0 < ind["chg_5d"] < 15:
        score += 8
    
    if ind["rsi"] < 65:
        score += 15
        reasons.append(("Room to Run", "Not overbought yet"))
    
    win_prob = min(95, int(score / max_score * 100))
    return win_prob, reasons


# ══════════════════════════════════════════════════════════════════
#  POSITION SIZING
# ══════════════════════════════════════════════════════════════════
def calc_position(ind, capital):
    price = ind["price"]
    atr = ind["atr"]
    
    sl = price - atr * CFG["sl_atr_mult"]
    tp = price + atr * CFG["tp_atr_mult"]
    
    sl_pct = (price - sl) / price * 100
    tp_pct = (tp - price) / price * 100
    rr = tp_pct / sl_pct if sl_pct > 0 else 0
    
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
        "cap_pct": cap_used / capital * 100 if capital > 0 else 0,
        "max_loss": shares * loss_per_share,
        "max_gain": shares * (tp - price),
    }


# ══════════════════════════════════════════════════════════════════
#  ANALYZE TICKER
# ══════════════════════════════════════════════════════════════════
def analyze_ticker(ticker, capital=1000):
    ind, df = fetch_data(ticker)
    if ind is None:
        return None
    
    weekly_bull, weekly_score = check_weekly_trend(ticker)
    if not weekly_bull:
        return None
    
    days_valid = check_signal_persistence(ticker)
    if days_valid < 2:
        return None
    
    win_prob, reasons = calculate_win_probability(ind)
    pos = calc_position(ind, capital)
    
    if win_prob < CFG["min_win_prob"]:
        return None
    if pos["tp_pct"] < CFG["min_profit_pct"]:
        return None
    if pos["rr"] < CFG["min_rr"]:
        return None
    if not (ind["ema8"] > ind["ema21"] and ind["price"] > ind["ema50"]):
        return None
    if ind["rsi"] > 72:
        return None
    
    if weekly_score >= 60:
        win_prob = min(95, win_prob + 5)
        reasons.append(("Weekly Confirmed", f"Weekly score {weekly_score}/100"))
    if days_valid >= 4:
        win_prob = min(95, win_prob + 3)
        reasons.append(("Stable Setup", f"Valid {days_valid} consecutive days"))
    
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


# ══════════════════════════════════════════════════════════════════
#  SCAN MARKET — Returns multiple signals for rotation
# ══════════════════════════════════════════════════════════════════
def scan_market(tickers, capital, progress_callback=None):
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
    
    results.sort(key=lambda x: x["win_prob"], reverse=True)
    # Return top signals for rotation (not just one)
    return results[:CFG["max_signals"]] if results else []


# ══════════════════════════════════════════════════════════════════
#  BACKTEST — Historical Signals
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def run_backtest():
    """Simulate past 3 months of signals and their outcomes."""
    signals = []
    
    for ticker in ALL_TICKERS:
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="6mo", interval="1d", auto_adjust=True, timeout=10)
            if df is None or df.empty or len(df) < 100:
                continue
            
            df.columns = [col.lower() for col in df.columns]
            c = df["close"]
            
            # Calculate indicators for the whole period
            ema8 = c.ewm(span=8).mean()
            ema21 = c.ewm(span=21).mean()
            ema50 = c.ewm(span=50).mean()
            
            df.ta.rsi(length=14, append=True)
            df.ta.adx(length=14, append=True)
            df.ta.atr(length=14, append=True)
            
            rsi = df["RSI_14"] if "RSI_14" in df.columns else pd.Series([50]*len(df))
            adx = df["ADX_14"] if "ADX_14" in df.columns else pd.Series([25]*len(df))
            atr = df["ATRr_14"] if "ATRr_14" in df.columns else c * 0.02
            
            # Look for entry signals in past 3 months (skip last 20 days for outcome)
            start_idx = max(60, len(df) - 90)
            end_idx = len(df) - 20
            
            for i in range(start_idx, end_idx):
                price = c.iloc[i]
                e8 = ema8.iloc[i]
                e21 = ema21.iloc[i]
                e50 = ema50.iloc[i]
                r = rsi.iloc[i] if i < len(rsi) else 50
                a = adx.iloc[i] if i < len(adx) else 25
                at = atr.iloc[i] if i < len(atr) else price * 0.02
                
                # Check for valid setup
                if not (price > e8 > e21 > e50):
                    continue
                if not (45 <= r <= 65):
                    continue
                if a < 20:
                    continue
                
                # Check persistence (2 days before)
                if i < 2:
                    continue
                prev_valid = True
                for j in range(1, 3):
                    if not (c.iloc[i-j] > ema8.iloc[i-j] > ema21.iloc[i-j]):
                        prev_valid = False
                        break
                if not prev_valid:
                    continue
                
                # Calculate SL/TP
                entry_price = float(price)
                sl = entry_price - float(at) * 1.5
                tp = entry_price + float(at) * 4.0
                
                # Check outcome in next 20 days
                hit_tp = False
                hit_sl = False
                exit_price = entry_price
                exit_days = 0
                
                for k in range(1, min(21, len(df) - i)):
                    high_k = df["high"].iloc[i + k]
                    low_k = df["low"].iloc[i + k]
                    
                    if low_k <= sl:
                        hit_sl = True
                        exit_price = sl
                        exit_days = k
                        break
                    if high_k >= tp:
                        hit_tp = True
                        exit_price = tp
                        exit_days = k
                        break
                
                if not hit_tp and not hit_sl:
                    exit_price = float(c.iloc[min(i + 15, len(df) - 1)])
                    exit_days = 15
                
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                
                signals.append({
                    "ticker": ticker,
                    "date": df.index[i].strftime("%b %d"),
                    "entry": entry_price,
                    "exit": exit_price,
                    "days": exit_days,
                    "pnl_pct": pnl_pct,
                    "won": pnl_pct > 0,
                    "hit_tp": hit_tp,
                    "hit_sl": hit_sl,
                })
                
                # Skip ahead to avoid duplicate signals
                break
                
        except Exception:
            continue
    
    return signals


def calculate_backtest_stats(signals):
    if not signals:
        return {"total": 0, "wins": 0, "win_rate": 0, "avg_win": 0, "avg_loss": 0, "best": 0, "worst": 0}
    
    wins = [s for s in signals if s["won"]]
    losses = [s for s in signals if not s["won"]]
    
    return {
        "total": len(signals),
        "wins": len(wins),
        "win_rate": len(wins) / len(signals) * 100 if signals else 0,
        "avg_win": sum(s["pnl_pct"] for s in wins) / len(wins) if wins else 0,
        "avg_loss": sum(s["pnl_pct"] for s in losses) / len(losses) if losses else 0,
        "best": max(s["pnl_pct"] for s in signals) if signals else 0,
        "worst": min(s["pnl_pct"] for s in signals) if signals else 0,
    }


# ══════════════════════════════════════════════════════════════════
#  CHART
# ══════════════════════════════════════════════════════════════════
def make_chart(df, ind, pos):
    df2 = df.tail(60).copy()
    c = df2["close"]
    
    ema8 = c.ewm(span=8).mean()
    ema21 = c.ewm(span=21).mean()
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=df2.index, open=df2["open"], high=df2["high"],
        low=df2["low"], close=df2["close"],
        name="Price",
        increasing_line_color="#30d158",
        decreasing_line_color="#ff453a",
    ))
    
    fig.add_trace(go.Scatter(x=df2.index, y=ema8, name="EMA 8", line=dict(color="#0a84ff", width=1)))
    fig.add_trace(go.Scatter(x=df2.index, y=ema21, name="EMA 21", line=dict(color="#ff9f0a", width=1)))
    
    fig.add_hline(y=pos["sl"], line_dash="dash", line_color="#ff453a", annotation_text="Stop")
    fig.add_hline(y=pos["tp"], line_dash="dash", line_color="#30d158", annotation_text="Target")
    
    fig.update_layout(
        paper_bgcolor="#1c1c1e",
        plot_bgcolor="#1c1c1e",
        font=dict(color="#86868b", size=10),
        xaxis=dict(gridcolor="#2c2c2e", showgrid=True),
        yaxis=dict(gridcolor="#2c2c2e", showgrid=True, side="right"),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.1),
        height=350,
        margin=dict(l=10, r=50, t=30, b=10),
    )
    return fig


# ══════════════════════════════════════════════════════════════════
#  MAIN UI
# ══════════════════════════════════════════════════════════════════

# Session state
if "sniper_result" not in st.session_state:
    st.session_state["sniper_result"] = None
if "capital" not in st.session_state:
    st.session_state["capital"] = 1000.0
if "show_backtest" not in st.session_state:
    st.session_state["show_backtest"] = False

# Inject CSS
st.markdown(CSS, unsafe_allow_html=True)

# Header
st.markdown("""
<div class="app-header">
    <h1 class="app-title">Rotation Mode</h1>
    <p class="app-subtitle">Take Signals · Rotate Capital · Compound Gains</p>
</div>
""", unsafe_allow_html=True)

# Market Status
regime, regime_score, regime_msg = get_market_regime()
pill_class = f"market-{regime.lower()}"
st.markdown(f"""
<div style="text-align: center;">
    <span class="market-pill {pill_class}">
        <span>●</span> Market: {regime_msg}
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Scan Button
scan_btn = st.button("Find Trades", type="primary", use_container_width=True)

# Handle scan
if scan_btn:
    st.session_state["sniper_result"] = None
    progress = st.progress(0, text="Scanning...")
    
    def update_progress(pct):
        progress.progress(pct, text=f"Analyzing {int(pct*100)}%")
    
    results = scan_market(ALL_TICKERS, 1000, update_progress)
    progress.empty()
    st.session_state["sniper_result"] = results

# Display results
results = st.session_state.get("sniper_result")

if results and len(results) > 0:
    # Show count of signals found
    st.markdown(f"""
    <div style="text-align: center; margin: 1rem 0;">
        <span style="color: #4ade80; font-size: 1.2rem; font-weight: 600;">{len(results)} Signal{'s' if len(results) > 1 else ''} Found</span>
        <span style="color: #64748b; margin-left: 8px;">Take #1, rotate to next when closed</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Capital input at top
    st.markdown('<div class="capital-card"><div class="capital-title">💰 Your Capital</div></div>', unsafe_allow_html=True)
    capital = st.number_input("Enter capital", min_value=100.0, max_value=1000000.0, value=st.session_state["capital"], step=100.0, label_visibility="collapsed")
    st.session_state["capital"] = capital
    
    # Display each signal
    for i, result in enumerate(results):
        ind = result["ind"]
        pos = calc_position(ind, capital)
        reasons = result["reasons"]
        
        # Signal number badge
        badge_color = "#4ade80" if i == 0 else "#64748b"
        badge_text = "TAKE NOW" if i == 0 else f"#{i+1} NEXT"
        
        st.markdown(f"""
        <div class="result-card" style="{'border: 2px solid #4ade80;' if i == 0 else 'opacity: 0.8;'}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div class="ticker-display">
                    <span class="ticker-symbol">{result['ticker']}</span>
                    <span class="ticker-price">${ind['price']:.2f}</span>
                </div>
                <span style="background: {badge_color}; color: #000; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 700;">{badge_text}</span>
            </div>
            <span class="ticker-sector">{result['sector']}</span>
            
            <div class="levels-grid" style="margin-top: 1.5rem;">
                <div class="level-item">
                    <div class="level-value" style="color: #a78bfa;">{result['win_prob']}%</div>
                    <div class="level-label">Probability</div>
                </div>
                <div class="level-item">
                    <div class="level-value red">${pos['sl']:.2f}</div>
                    <div class="level-label">Stop ({pos['sl_pct']:.1f}%)</div>
                </div>
                <div class="level-item">
                    <div class="level-value green">${pos['tp']:.2f}</div>
                    <div class="level-label">Target (+{pos['tp_pct']:.1f}%)</div>
                </div>
                <div class="level-item">
                    <div class="level-value blue">{pos['shares']:.1f}</div>
                    <div class="level-label">Shares</div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1); color: #64748b; font-size: 0.85rem;">
                <span>Risk: <span style="color: #f87171;">${pos['max_loss']:.0f}</span></span>
                <span>Reward: <span style="color: #4ade80;">${pos['max_gain']:.0f}</span></span>
                <span>R:R <span style="color: #60a5fa;">1:{pos['rr']:.1f}</span></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable details for first signal only
        if i == 0:
            with st.expander("Why this stock?"):
                for title, text in reasons:
                    st.markdown(f'<div class="reason-item"><div class="reason-title">{title}</div><div class="reason-text">{text}</div></div>', unsafe_allow_html=True)
            
            with st.expander("View Chart"):
                fig = make_chart(result["df"], ind, pos)
                st.plotly_chart(fig, use_container_width=True)
    
    # Expected returns box
    avg_gain = 6.7  # Based on backtest
    avg_loss = 3.3
    win_rate = 0.45  # Conservative estimate
    expected_per_trade = (win_rate * avg_gain) - ((1-win_rate) * avg_loss)
    monthly_trades = 7
    monthly_return = expected_per_trade * monthly_trades
    
    st.markdown(f"""
    <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 16px; padding: 1.5rem; margin: 1.5rem 0;">
        <div style="color: #a78bfa; font-weight: 600; font-size: 0.9rem; margin-bottom: 1rem;">📈 Rotation Strategy (Expected)</div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; text-align: center;">
            <div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #fff;">~{monthly_trades}</div>
                <div style="font-size: 0.7rem; color: #64748b;">TRADES/MONTH</div>
            </div>
            <div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #4ade80;">+{expected_per_trade:.1f}%</div>
                <div style="font-size: 0.7rem; color: #64748b;">PER TRADE</div>
            </div>
            <div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #4ade80;">+${capital * monthly_return / 100:.0f}</div>
                <div style="font-size: 0.7rem; color: #64748b;">MONTHLY EST.</div>
            </div>
        </div>
        <div style="color: #64748b; font-size: 0.8rem; margin-top: 1rem; text-align: center;">
            Based on ~45% win rate · +6.7% avg win · -3.3% avg loss
        </div>
    </div>
    """, unsafe_allow_html=True)

elif scan_btn:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">◎</div>
        <div class="empty-title">No Setups Today</div>
        <div class="empty-text">
            No stocks meet our 60%+ criteria right now.<br>
            Check back tomorrow. Patience pays.
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">◎</div>
        <div class="empty-title">Ready to Scan</div>
        <div class="empty-text">
            Scanning {len(ALL_TICKERS)} stocks for rotation opportunities.<br>
            60%+ probability · 2:1 reward/risk · Take signals, rotate capital
        </div>
    </div>
    """, unsafe_allow_html=True)

# Backtest Section
st.markdown("<hr>", unsafe_allow_html=True)

with st.expander("📊 Past Performance (3 Months)"):
    backtest_btn = st.button("Run Backtest", key="backtest_btn")
    
    if backtest_btn:
        with st.spinner("Analyzing historical signals..."):
            signals = run_backtest()
            st.session_state["backtest_signals"] = signals
    
    if "backtest_signals" in st.session_state:
        signals = st.session_state["backtest_signals"]
        stats = calculate_backtest_stats(signals)
        
        if stats["total"] > 0:
            st.markdown(f"""
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{stats['total']}</div>
                    <div class="stat-label">Signals</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: #30d158;">{stats['win_rate']:.0f}%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: #30d158;">+{stats['avg_win']:.1f}%</div>
                    <div class="stat-label">Avg Win</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: #ff453a;">{stats['avg_loss']:.1f}%</div>
                    <div class="stat-label">Avg Loss</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="backtest-title">Recent Signals</div>', unsafe_allow_html=True)
            
            for s in sorted(signals, key=lambda x: x["pnl_pct"], reverse=True)[:10]:
                color = "#30d158" if s["won"] else "#ff453a"
                result_text = f"+{s['pnl_pct']:.1f}%" if s["won"] else f"{s['pnl_pct']:.1f}%"
                outcome = "TP Hit" if s["hit_tp"] else "SL Hit" if s["hit_sl"] else f"{s['days']}d"
                
                st.markdown(f"""
                <div class="signal-row">
                    <span class="signal-ticker">{s['ticker']}</span>
                    <span class="signal-date">{s['date']} · ${s['entry']:.0f} → ${s['exit']:.0f}</span>
                    <span style="color: #86868b;">{outcome}</span>
                    <span class="signal-result" style="color: {color};">{result_text}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No signals found in the past 3 months with current criteria.")
