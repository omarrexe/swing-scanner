"""
Swing Trading Scanner — Streamlit App
Beginner-friendly US stock market scanner with full explanations.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# ──────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Swing Trading Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────
#  CUSTOM CSS
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem; font-weight: 700;
        background: linear-gradient(90deg, #00C851, #007bff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header { color: #888; font-size: 0.95rem; margin-bottom: 1.5rem; }
    .signal-strong-buy {
        background: #003d1a; border: 1px solid #00C851;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #00C851; font-weight: 700; font-size: 1.05rem;
    }
    .signal-buy {
        background: #002b10; border: 1px solid #28a745;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #28a745; font-weight: 600;
    }
    .signal-wait {
        background: #2b2500; border: 1px solid #ffc107;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #ffc107;
    }
    .signal-avoid {
        background: #2b0000; border: 1px solid #dc3545;
        border-radius: 8px; padding: 0.8rem 1rem;
        color: #dc3545;
    }
    .metric-card {
        background: #1a1a2e; border: 1px solid #333;
        border-radius: 10px; padding: 1rem;
        text-align: center;
    }
    .check-pass { color: #00C851; font-weight: 600; }
    .check-fail { color: #dc3545; }
    .explanation-box {
        background: #0d1117; border-left: 3px solid #007bff;
        border-radius: 4px; padding: 0.8rem 1rem;
        color: #ccc; font-size: 0.88rem; margin: 0.5rem 0;
    }
    .trade-box {
        background: #0a1628; border: 1px solid #007bff;
        border-radius: 10px; padding: 1.2rem;
    }
    .stop-loss-box {
        background: #1a0a0a; border: 1px solid #dc3545;
        border-radius: 8px; padding: 0.8rem; text-align: center;
    }
    .take-profit-box {
        background: #0a1a0a; border: 1px solid #00C851;
        border-radius: 8px; padding: 0.8rem; text-align: center;
    }
    .stButton > button {
        width: 100%; border-radius: 8px;
        font-weight: 600; font-size: 0.95rem;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #333; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  WATCHLIST — Curated liquid US stocks great for swing trading
# ──────────────────────────────────────────────────────────────────
WATCHLIST = {
    "Tech — Large Cap": [
        "AAPL","MSFT","NVDA","AMD","META","GOOGL","TSLA","AMZN",
        "NFLX","ADBE","CRM","ORCL","QCOM","AVGO","INTC","MU","PLTR",
    ],
    "Finance": [
        "JPM","BAC","GS","MS","V","MA","AXP","WFC","C","BLK",
    ],
    "Growth / Momentum": [
        "UBER","COIN","HOOD","SOFI","RBLX","SNAP","LYFT","ABNB","DASH",
    ],
    "Crypto / Mining": [
        "IREN","MARA","RIOT","CLSK","CIFR",
    ],
    "Healthcare": [
        "LLY","PFE","ABBV","MRK","JNJ","GILD","AMGN",
    ],
    "Energy / Materials": [
        "XOM","CVX","SLB","FCX","NEM","AA","MOS",
    ],
    "ETFs — Safer Options": [
        "SPY","QQQ","IWM","TQQQ","SOXL","ARKK",
    ],
}
ALL_TICKERS = [t for group in WATCHLIST.values() for t in group]

# ──────────────────────────────────────────────────────────────────
#  SETTINGS
# ──────────────────────────────────────────────────────────────────
CFG = {
    "sl_atr_mult"      : 1.5,
    "tp_atr_mult"      : 3.5,
    "min_rr"           : 2.0,
    "min_signals"      : 4,
    "rsi_min"          : 35,
    "rsi_max"          : 68,
    "risk_per_trade_pct": 1.5,
    "max_position_pct" : 30.0,
}

# ──────────────────────────────────────────────────────────────────
#  DATA & INDICATORS
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)   # cache for 5 minutes
def fetch_data(ticker: str):
    try:
        t    = yf.Ticker(ticker)
        df   = t.history(period="6mo", interval="1d", auto_adjust=True)
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
    BULL = ["beat","raised","upgrade","outperform","growth","record","profit",
            "surge","rally","deal","launch","revenue","buyback","expand","strong"]
    BEAR = ["miss","cut","downgrade","underperform","loss","weak","decline",
            "investigation","lawsuit","layoffs","warning","bankruptcy","fraud"]
    score, titles = 0, []
    for n in (news_list or [])[:8]:
        title = n.get("content", {}).get("title", "") or n.get("title", "")
        if not title:
            continue
        tl = title.lower()
        score += sum(1 for w in BULL if w in tl)
        score -= sum(1 for w in BEAR if w in tl)
        titles.append(title[:70])
    label  = "🟢 Positive" if score > 1 else ("🔴 Negative" if score < -1 else "⚪ Neutral")
    latest = titles[0] if titles else "No recent headlines"
    return score, label, latest


def run_signals(ind, ns):
    """7 scientific checks with plain-English explanations."""
    checks = []

    # 1. Trend
    if ind["ema8"] > ind["ema21"] > ind["ema50"]:
        checks.append({
            "name": "Trend (EMA Stack)",
            "pass": True,
            "result": f"EMA8 ({ind['ema8']:.2f}) > EMA21 ({ind['ema21']:.2f}) > EMA50 ({ind['ema50']:.2f})",
            "reason": "All moving averages aligned upward — strong uptrend confirmed.",
            "explain": "EMA = Exponential Moving Average. When short-term averages are above long-term ones, the stock is trending up. Think of it like a moving average of the price that reacts faster to recent changes.",
        })
    elif ind["ema8"] > ind["ema21"]:
        checks.append({
            "name": "Trend (EMA Stack)",
            "pass": True,
            "result": f"EMA8 ({ind['ema8']:.2f}) > EMA21 ({ind['ema21']:.2f})",
            "reason": "Short-term bullish — EMA50 not yet aligned.",
            "explain": "Partial uptrend. The short-term trend is up, but the medium-term hasn't confirmed yet. Still usable as a signal.",
        })
    else:
        checks.append({
            "name": "Trend (EMA Stack)",
            "pass": False,
            "result": f"EMA8 ({ind['ema8']:.2f}) < EMA21 ({ind['ema21']:.2f})",
            "reason": "Bearish trend — price is falling on short-term timeframe.",
            "explain": "When EMA8 is below EMA21, the recent price action is weaker than the 21-day trend. This means downward momentum.",
        })

    # 2. RSI
    rising = ind["rsi"] > ind["rsi_prev"]
    if CFG["rsi_min"] <= ind["rsi"] <= CFG["rsi_max"] and rising:
        checks.append({
            "name": "RSI Momentum",
            "pass": True,
            "result": f"RSI = {ind['rsi']:.1f} (rising from {ind['rsi_prev']:.1f})",
            "reason": "RSI in healthy buy zone and rising — buying pressure is building.",
            "explain": "RSI (Relative Strength Index) measures momentum on a 0–100 scale. Below 30 = oversold (too cheap). Above 70 = overbought (too expensive). Between 35–68 while rising = ideal entry zone.",
        })
    elif ind["rsi"] > 70:
        checks.append({
            "name": "RSI Momentum",
            "pass": False,
            "result": f"RSI = {ind['rsi']:.1f} — OVERBOUGHT",
            "reason": "RSI above 70 — the stock may be overextended and due for a pullback.",
            "explain": "When RSI is above 70, the stock has been bought too aggressively. Price often pulls back after this. It's risky to enter here.",
        })
    elif ind["rsi"] < 30:
        checks.append({
            "name": "RSI Momentum",
            "pass": False,
            "result": f"RSI = {ind['rsi']:.1f} — OVERSOLD",
            "reason": "RSI below 30 — wait for a bounce confirmation before entering.",
            "explain": "When RSI is below 30, the stock has been sold heavily. While it might bounce, we need confirmation (RSI starting to rise) before entering.",
        })
    else:
        checks.append({
            "name": "RSI Momentum",
            "pass": False,
            "result": f"RSI = {ind['rsi']:.1f} ({'rising' if rising else 'falling'})",
            "reason": "RSI not in optimal buy zone or falling.",
            "explain": "RSI needs to be between 35–68 AND rising to indicate good entry timing.",
        })

    # 3. MACD
    if ind["macd_h"] > 0 and ind["macd_h"] > ind["macd_prev"]:
        checks.append({
            "name": "MACD",
            "pass": True,
            "result": f"Histogram = +{ind['macd_h']:.3f} (rising)",
            "reason": "MACD positive and accelerating — buyers are gaining strength.",
            "explain": "MACD measures the difference between two moving averages. When the histogram (bar chart) is positive and growing, buying momentum is increasing. This is one of the strongest confirmation signals.",
        })
    elif ind["macd_h"] > 0:
        checks.append({
            "name": "MACD",
            "pass": True,
            "result": f"Histogram = +{ind['macd_h']:.3f} (slowing)",
            "reason": "MACD positive but momentum is slowing down.",
            "explain": "Buying pressure exists but is weakening. Still a positive sign, but less strong than a rising histogram.",
        })
    else:
        checks.append({
            "name": "MACD",
            "pass": False,
            "result": f"Histogram = {ind['macd_h']:.3f} (negative)",
            "reason": "MACD negative — sellers currently in control.",
            "explain": "A negative MACD histogram means selling momentum is stronger than buying. Not a good time to enter a long position.",
        })

    # 4. Volume
    if ind["vol_r"] >= 1.5:
        checks.append({
            "name": "Volume",
            "pass": True,
            "result": f"Volume = {ind['vol_r']:.1f}x the 20-day average",
            "reason": "Strong volume — institutions and big players are actively buying.",
            "explain": "Volume is the number of shares traded. When volume is significantly above average, it means large institutions (banks, funds) are involved. Their buying pushes prices higher and confirms the move.",
        })
    elif ind["vol_r"] >= 1.1:
        checks.append({
            "name": "Volume",
            "pass": True,
            "result": f"Volume = {ind['vol_r']:.1f}x the 20-day average",
            "reason": "Moderate volume — decent buying interest.",
            "explain": "Volume is above average, suggesting legitimate buying activity. Not extremely strong, but acceptable for a swing trade entry.",
        })
    else:
        checks.append({
            "name": "Volume",
            "pass": False,
            "result": f"Volume = {ind['vol_r']:.1f}x average (below average)",
            "reason": "Low volume — the price move is not confirmed by buyers.",
            "explain": "Low volume means few participants are trading. Price moves on low volume are often reversed quickly. We need volume confirmation to trust the signal.",
        })

    # 5. Bollinger Bands
    if 0.25 <= ind["bb_pos"] <= 0.72:
        checks.append({
            "name": "Bollinger Bands",
            "pass": True,
            "result": f"Price at {ind['bb_pos']*100:.0f}% of the band",
            "reason": "Price in healthy middle zone — room to move up without being overextended.",
            "explain": "Bollinger Bands show the normal price range (±2 standard deviations from the 20-day average). When price is in the middle (25–72%), it has room to move up. Near the top band (>88%) means overextended.",
        })
    elif ind["bb_pos"] > 0.88:
        checks.append({
            "name": "Bollinger Bands",
            "pass": False,
            "result": f"Price at {ind['bb_pos']*100:.0f}% — near upper band",
            "reason": "Price stretched near the top of the band — risky entry, may pull back.",
            "explain": "When price is near the upper Bollinger Band, it's statistically overextended. Prices tend to revert toward the middle, meaning a pullback is likely.",
        })
    else:
        checks.append({
            "name": "Bollinger Bands",
            "pass": False,
            "result": f"Price at {ind['bb_pos']*100:.0f}% — near lower band",
            "reason": "Price near the bottom of the band — wait for reversal confirmation.",
            "explain": "Price near the lower band can mean oversold, but we need to see it start recovering before entering. Entering too early in a downtrend can be costly.",
        })

    # 6. VWAP
    vwap_gap = (ind["price"] - ind["vwap"]) / ind["vwap"] * 100
    if ind["price"] > ind["vwap"]:
        checks.append({
            "name": "VWAP",
            "pass": True,
            "result": f"Price {vwap_gap:+.1f}% above VWAP ({ind['vwap']:.2f})",
            "reason": "Price above VWAP — buyers are in control today.",
            "explain": "VWAP (Volume Weighted Average Price) is the average price weighted by volume. It's the 'fair price' institutions use. When price is above it, buyers are willing to pay more than fair value — a bullish sign.",
        })
    else:
        checks.append({
            "name": "VWAP",
            "pass": False,
            "result": f"Price {vwap_gap:+.1f}% below VWAP ({ind['vwap']:.2f})",
            "reason": "Price below VWAP — sellers in control, avoid entering long.",
            "explain": "When price is below VWAP, sellers are accepting less than fair value — a bearish sign. Institutions often use VWAP as a benchmark, so price below it suggests selling pressure.",
        })

    # 7. News
    if ns > 1:
        checks.append({
            "name": "News Catalyst",
            "pass": True,
            "result": f"Positive news sentiment (score: +{ns})",
            "reason": "Strong positive headlines today — fundamental support for the move.",
            "explain": "News can act as a catalyst (trigger) for price movement. Positive news like earnings beats, upgrades, or new contracts gives buyers more reason to push the price higher.",
        })
    elif ns > 0:
        checks.append({
            "name": "News Catalyst",
            "pass": True,
            "result": f"Mild positive news (score: +{ns})",
            "reason": "Slight positive news tailwind.",
            "explain": "Some positive news present, though not major. Acts as a minor supporting factor.",
        })
    elif ns < -1:
        checks.append({
            "name": "News Catalyst",
            "pass": False,
            "result": f"Negative news (score: {ns})",
            "reason": "Negative headlines — fundamental headwind, be very careful.",
            "explain": "Negative news like earnings misses, lawsuits, or downgrades can push prices sharply lower. Even if technical signals are good, bad news can override everything.",
        })
    else:
        checks.append({
            "name": "News Catalyst",
            "pass": False,
            "result": "No significant news",
            "reason": "No news catalyst today — purely technical trade.",
            "explain": "Without a news catalyst, the trade relies entirely on technical signals. Not necessarily bad, but a catalyst would increase the probability of a successful move.",
        })

    return checks


def calc_position(ind, capital):
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


def make_decision(ind, checks, pos):
    score    = sum(1 for c in checks if c["pass"])
    trend_ok = ind["ema8"] > ind["ema21"] and ind["price"] > ind["ema50"]
    blockers = []

    if not trend_ok:
        blockers.append("Overall trend is bearish — we never trade against the trend")
    if pos and pos["rr"] < CFG["min_rr"]:
        blockers.append(f"Risk:Reward ratio 1:{pos['rr']:.1f} is below our minimum of 1:{CFG['min_rr']}")
    if not (0.5 <= ind["atr_pct"] <= 10.0):
        blockers.append(f"Volatility {ind['atr_pct']:.1f}%/day is outside safe range (0.5–10%)")

    if blockers:
        return "SKIP", score, blockers
    if score >= 6:
        return "STRONG BUY", score, []
    elif score >= CFG["min_signals"]:
        return "BUY", score, []
    elif score <= 2:
        return "AVOID", score, []
    else:
        return "WAIT", score, []

# ──────────────────────────────────────────────────────────────────
#  CHART
# ──────────────────────────────────────────────────────────────────
def make_chart(df, ind, pos, ticker):
    df2 = df.tail(90).copy()
    c   = df2["close"]

    ema8  = c.ewm(span=8,  adjust=False).mean()
    ema21 = c.ewm(span=21, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df2.index, open=df2["open"], high=df2["high"],
        low=df2["low"], close=df2["close"],
        name="Price",
        increasing_line_color="#00C851",
        decreasing_line_color="#dc3545",
    ))

    # EMAs
    fig.add_trace(go.Scatter(x=df2.index, y=ema8,  name="EMA 8",  line=dict(color="#00bfff",  width=1.5)))
    fig.add_trace(go.Scatter(x=df2.index, y=ema21, name="EMA 21", line=dict(color="#ff8c00",  width=1.5)))
    fig.add_trace(go.Scatter(x=df2.index, y=ema50, name="EMA 50", line=dict(color="#9370db",  width=1.5)))

    # Stop Loss / Take Profit lines
    if pos:
        last_date = df2.index[-1]
        future    = last_date + timedelta(days=15)
        fig.add_hline(y=pos["sl"], line_dash="dash", line_color="#dc3545",
                      annotation_text=f"Stop Loss ${pos['sl']:.2f}", annotation_position="right")
        fig.add_hline(y=pos["tp"], line_dash="dash", line_color="#00C851",
                      annotation_text=f"Take Profit ${pos['tp']:.2f}", annotation_position="right")

    fig.update_layout(
        title=f"{ticker} — Last 90 Days",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="#ccc"),
        xaxis=dict(gridcolor="#222", showgrid=True),
        yaxis=dict(gridcolor="#222", showgrid=True, title="Price (USD)"),
        legend=dict(bgcolor="#0d1117"),
        xaxis_rangeslider_visible=False,
        height=420,
        margin=dict(l=40, r=40, t=50, b=30),
    )
    return fig

# ──────────────────────────────────────────────────────────────────
#  SIDEBAR
# ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    capital = st.number_input(
        "💵 Your Total Capital (USD)",
        min_value=100.0,
        max_value=1_000_000.0,
        value=1000.0,
        step=100.0,
        help="Enter your TOTAL available money. The scanner will size every trade based on this.",
    )

    st.markdown(f"""
    <div style='background:#0a1628;border:1px solid #333;border-radius:8px;padding:0.8rem;font-size:0.85rem;color:#aaa'>
    <b style='color:#fff'>How your capital is protected:</b><br><br>
    Max risk per trade: <b style='color:#00C851'>${capital * 1.5 / 100:.0f}</b> (1.5%)<br>
    Max per position: <b style='color:#00bfff'>${capital * 30 / 100:.0f}</b> (30%)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 📂 Select Stock Groups")
    selected_groups = []
    for group in WATCHLIST:
        if st.checkbox(group, value=True):
            selected_groups.append(group)

    st.markdown("---")
    st.markdown("### 🔍 Or search a specific stock")
    custom_ticker = st.text_input("Enter ticker symbol", placeholder="e.g. AAPL, NVDA, TSLA").upper().strip()

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.78rem;color:#666;line-height:1.6'>
    <b>⚠️ Disclaimer</b><br>
    This tool is for educational purposes only.
    Not financial advice. Always do your own research
    before investing real money.
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  MAIN CONTENT
# ──────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">📈 Swing Trading Scanner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">US Stock Market · Scientific Analysis · Beginner Friendly · Data updates every 5 minutes</div>', unsafe_allow_html=True)

# ── What is swing trading (expandable) ────────────────────────────
with st.expander("📚 What is Swing Trading? (click to learn)", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🕐 How long?**
        You buy a stock today and sell it in **2–10 days** when it either:
        - Hits your Take Profit → you made money ✅
        - Hits your Stop Loss → you exit to protect capital 🛡️
        """)
    with col2:
        st.markdown("""
        **🔬 How does this scanner work?**
        It runs **7 scientific checks** on each stock.
        If 4 or more pass, it signals a potential buy.
        Every decision is explained in plain English.
        """)
    with col3:
        st.markdown("""
        **💰 How is my money protected?**
        The **1.5% rule**: never risk more than 1.5% of your
        total capital on a single trade. This means even 10
        losing trades in a row only costs you ~15%.
        """)

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Market Scanner", "📊 Analyze a Specific Stock"])

# ════════════════════════════════════════════════════════════════
#  DETAIL VIEW FUNCTION
# ════════════════════════════════════════════════════════════════
def _show_detail(r, capital):
    ticker = r["ticker"]
    ind    = r["ind"]
    pos    = r["pos"]
    checks = r["checks"]
    action = r["action"]
    score  = r["score"]

    st.markdown(f"## 📊 Full Analysis — {ticker}")
    st.markdown(f"*Live data as of {datetime.now().strftime('%H:%M:%S')} · {datetime.now().strftime('%Y-%m-%d')}*")

    # Signal badge
    if action == "STRONG BUY":
        st.markdown(f'<div class="signal-strong-buy" style="font-size:1.3rem;padding:1rem">🟢 STRONG BUY — {score}/7 signals confirmed — High-conviction setup</div>', unsafe_allow_html=True)
    elif action == "BUY":
        st.markdown(f'<div class="signal-buy" style="font-size:1.2rem;padding:1rem">🟢 BUY — {score}/7 signals confirmed — Valid swing trade setup</div>', unsafe_allow_html=True)
    elif action == "WAIT":
        st.markdown(f'<div class="signal-wait" style="font-size:1.1rem;padding:1rem">🟡 WAIT — {score}/7 signals — Setup is developing, check again soon</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="signal-avoid" style="font-size:1.1rem;padding:1rem">🔴 AVOID — Only {score}/7 signals — Conditions not right for entry</div>', unsafe_allow_html=True)

    # News
    ns_icon = "🟢" if r["ns"] > 0 else ("🔴" if r["ns"] < 0 else "⚪")
    st.markdown(f"**News:** {ns_icon} {r['nl']}  ·  *{r['headline'][:80]}*")
    st.markdown("---")

    # Chart
    if r.get("df") is not None:
        fig = make_chart(r["df"], ind, pos if action in ("STRONG BUY","BUY") else None, ticker)
        st.plotly_chart(fig, use_container_width=True)

    # 7 Signals
    st.markdown("### 🔬 The 7 Scientific Checks — Why This Stock?")
    st.markdown("*Every check has a plain-English explanation. Click the ▶ to learn more.*")

    passed = sum(1 for c in checks if c["pass"])
    st.progress(passed / 7, text=f"{passed}/7 checks passed")

    for i, chk in enumerate(checks, 1):
        icon = "✅" if chk["pass"] else "❌"
        with st.expander(f"{icon} **Check {i}: {chk['name']}** — {chk['result']}", expanded=chk["pass"]):
            st.markdown(f"**{'✅ PASSED' if chk['pass'] else '❌ FAILED'}:** {chk['reason']}")
            st.markdown(f'<div class="explanation-box">💡 <b>What does this mean?</b><br>{chk["explain"]}</div>', unsafe_allow_html=True)

    # Trade Plan
    if pos and action in ("STRONG BUY", "BUY"):
        st.markdown("---")
        st.markdown("### 💰 Your Trade Plan")
        st.markdown(f"*Based on your total capital of **${capital:,.0f}***")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
            <div style='color:#888;font-size:0.8rem'>ENTRY PRICE</div>
            <div style='font-size:1.8rem;font-weight:700;color:#fff'>${ind['price']:.2f}</div>
            <div style='color:#888;font-size:0.8rem'>Buy at market price</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stop-loss-box">
            <div style='color:#dc3545;font-size:0.8rem;font-weight:600'>🛑 STOP LOSS</div>
            <div style='font-size:1.8rem;font-weight:700;color:#dc3545'>${pos['sl']:.2f}</div>
            <div style='color:#dc3545;font-size:0.85rem'>-{pos['sl_pct']:.1f}% · Exit here to protect capital</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="take-profit-box">
            <div style='color:#00C851;font-size:0.8rem;font-weight:600'>🎯 TAKE PROFIT</div>
            <div style='font-size:1.8rem;font-weight:700;color:#00C851'>${pos['tp']:.2f}</div>
            <div style='color:#00C851;font-size:0.85rem'>+{pos['tp_pct']:.1f}% · Your profit target</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Risk : Reward", f"1 : {pos['rr']:.1f}", help="For every $1 you risk, you can gain this much")
        p2.metric("Shares to Buy", f"{pos['shares']:.4f}", help="Exact number of shares based on your capital and risk rules")
        p3.metric("Capital Used", f"${pos['cap_used']:.0f} ({pos['cap_pct']:.1f}%)", help="How much of your capital this trade uses")
        p4.metric("Max Loss", f"${pos['max_loss']:.0f}", delta=f"-{CFG['risk_per_trade_pct']}% of capital", delta_color="inverse")

        with st.expander("💡 How was this trade plan calculated?"):
            st.markdown(f"""
            **Step 1 — Stop Loss** = Entry price − (ATR × 1.5)
            - ATR (Average True Range) = how much the stock moves per day on average = **${ind['atr']:.2f}**
            - Stop Loss = ${ind['price']:.2f} − (${ind['atr']:.2f} × 1.5) = **${pos['sl']:.2f}**
            - This gives enough room for normal daily fluctuation without exiting too early.

            **Step 2 — Take Profit** = Entry price + (ATR × 3.5)
            - Take Profit = ${ind['price']:.2f} + (${ind['atr']:.2f} × 3.5) = **${pos['tp']:.2f}**
            - This ensures our potential gain is always at least 2× our potential loss (Risk:Reward ≥ 2).

            **Step 3 — Position Size** (how many shares to buy)
            - Max loss allowed = ${capital:,.0f} × 1.5% = **${capital*1.5/100:.0f}**
            - Loss per share = ${ind['price']:.2f} − ${pos['sl']:.2f} = **${ind['price']-pos['sl']:.2f}**
            - Shares = ${capital*1.5/100:.0f} ÷ ${ind['price']-pos['sl']:.2f} = **{pos['shares']:.4f} shares**
            - Also capped at 30% of capital (${capital*30/100:.0f}) to avoid overexposure.

            **The 1.5% Rule** protects you: even if you take 10 losing trades in a row,
            you only lose ~15% of your total capital.
            """)

        st.info("📌 **Exit rule**: Sell when price hits your Take Profit **OR** Stop Loss. Max hold time: 10 days.")

    if r.get("blockers"):
        st.markdown("---")
        st.warning("⚠️ **Why this stock was flagged:**")
        for b in r["blockers"]:
            st.markdown(f"- {b}")



# ════════════════════════════════════════════════════════════════
#  TAB 1 — MARKET SCANNER
# ════════════════════════════════════════════════════════════════
with tab1:
    tickers_to_scan = []
    for g in selected_groups:
        tickers_to_scan.extend(WATCHLIST[g])
    tickers_to_scan = list(dict.fromkeys(tickers_to_scan))  # deduplicate

    st.markdown(f"**{len(tickers_to_scan)} stocks** selected from your chosen groups.")

    col_scan, col_info = st.columns([2, 3])
    with col_scan:
        scan_btn = st.button("🚀 Start Scan", type="primary", use_container_width=True)
    with col_info:
        st.markdown(f"<div style='color:#888;font-size:0.85rem;padding-top:0.6rem'>"
                    f"⏱ Estimated time: ~{max(1, len(tickers_to_scan)//20)} minutes "
                    f"· Data is cached for 5 minutes</div>", unsafe_allow_html=True)

    if scan_btn:
        st.session_state["scan_results"] = None
        st.session_state["selected_ticker"] = None

        results = []
        progress_bar = st.progress(0, text="Starting scan...")
        status_text  = st.empty()

        for i, ticker in enumerate(tickers_to_scan):
            progress = (i + 1) / len(tickers_to_scan)
            progress_bar.progress(progress, text=f"Scanning {ticker}... ({i+1}/{len(tickers_to_scan)})")

            ind, df, news = fetch_data(ticker)
            if ind is None:
                continue

            ns, nl, headline = news_score(news)
            checks  = run_signals(ind, ns)
            pos     = calc_position(ind, capital)
            action, score, blockers = make_decision(ind, checks, pos)

            if action != "SKIP":
                results.append({
                    "ticker"  : ticker,
                    "ind"     : ind,
                    "df"      : df,
                    "checks"  : checks,
                    "pos"     : pos,
                    "action"  : action,
                    "score"   : score,
                    "blockers": blockers,
                    "ns"      : ns,
                    "nl"      : nl,
                    "headline": headline,
                })

        progress_bar.empty()
        status_text.empty()

        # Sort by score
        order = {"STRONG BUY": 0, "BUY": 1, "WAIT": 2, "AVOID": 3}
        results.sort(key=lambda x: (order.get(x["action"], 9), -x["score"]))
        st.session_state["scan_results"] = results

    # ── Display results ───────────────────────────────────────────
    if st.session_state.get("scan_results") is not None:
        results = st.session_state["scan_results"]
        tradeable = [r for r in results if r["action"] in ("STRONG BUY", "BUY")]
        waiting   = [r for r in results if r["action"] == "WAIT"]

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stocks Scanned",  len(results))
        m2.metric("🟢 Trade Ready",  len(tradeable))
        m3.metric("🟡 Watching",     len(waiting))
        m4.metric("Capital",         f"${capital:,.0f}")

        st.markdown("---")
        st.markdown("### Results — click a row to see full analysis")

        for r in results:
            action = r["action"]
            score  = r["score"]
            ind    = r["ind"]
            chg_c  = "color:#00C851" if ind["chg_1d"] >= 0 else "color:#dc3545"
            chg_s  = f"+{ind['chg_1d']:.2f}%" if ind["chg_1d"] >= 0 else f"{ind['chg_1d']:.2f}%"

            if action == "STRONG BUY":
                sig_class = "signal-strong-buy"
            elif action == "BUY":
                sig_class = "signal-buy"
            elif action == "WAIT":
                sig_class = "signal-wait"
            else:
                sig_class = "signal-avoid"

            col_sig, col_info2, col_btn = st.columns([2, 4, 1.5])

            with col_sig:
                st.markdown(f"""
                <div class="{sig_class}">
                {action} &nbsp; {score}/7
                </div>
                """, unsafe_allow_html=True)

            with col_info2:
                st.markdown(f"""
                <div style='padding-top:0.5rem'>
                <b style='font-size:1.1rem'>{r['ticker']}</b>
                &nbsp;&nbsp;
                <span style='font-size:1.05rem'>${ind['price']:.2f}</span>
                &nbsp;&nbsp;
                <span style='{chg_c}'>{chg_s} today</span>
                &nbsp;&nbsp;
                <span style='color:#888;font-size:0.85rem'>ATR: {ind['atr_pct']:.1f}%/day · RSI: {ind['rsi']:.0f} · Vol: {ind['vol_r']:.1f}x</span>
                </div>
                """, unsafe_allow_html=True)

            with col_btn:
                if st.button("Analyze →", key=f"btn_{r['ticker']}"):
                    st.session_state["selected_ticker"] = r["ticker"]
                    st.session_state["selected_result"] = r

            st.markdown('<div style="border-top:1px solid #1a1a1a;margin:2px 0"></div>', unsafe_allow_html=True)

        # ── Detail view ───────────────────────────────────────────
        if st.session_state.get("selected_result"):
            r = st.session_state["selected_result"]
            st.markdown("---")
            _show_detail(r, capital)

# ════════════════════════════════════════════════════════════════
#  TAB 2 — SINGLE STOCK ANALYSIS
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🔎 Analyze Any US Stock")
    st.markdown("Enter any ticker to get a complete scientific analysis right now.")

    search_col, btn_col = st.columns([3, 1])
    with search_col:
        ticker_input = st.text_input(
            "Stock ticker",
            value=custom_ticker or "",
            placeholder="e.g. AAPL, NVDA, TSLA, IREN, MU",
            label_visibility="collapsed",
        ).upper().strip()
    with btn_col:
        analyze_btn = st.button("Analyze Now →", type="primary", use_container_width=True)

    if ticker_input and analyze_btn:
        with st.spinner(f"Fetching live data for {ticker_input}..."):
            # Clear cache for this ticker to get fresh data
            fetch_data.clear()
            ind, df, news = fetch_data(ticker_input)

        if ind is None:
            st.error(f"Could not fetch data for **{ticker_input}**. Please check the ticker symbol and try again.")
            st.markdown("Common issues: ticker not found, delisted stock, or connection error.")
        else:
            ns, nl, headline = news_score(news)
            checks  = run_signals(ind, ns)
            pos     = calc_position(ind, capital)
            action, score, blockers = make_decision(ind, checks, pos)

            result = {
                "ticker"  : ticker_input,
                "ind"     : ind,
                "df"      : df,
                "checks"  : checks,
                "pos"     : pos,
                "action"  : action,
                "score"   : score,
                "blockers": blockers,
                "ns"      : ns,
                "nl"      : nl,
                "headline": headline,
            }
            _show_detail(result, capital)


# ──────────────────────────────────────────────────────────────────
#  SESSION STATE INIT
# ──────────────────────────────────────────────────────────────────
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = None
if "selected_result" not in st.session_state:
    st.session_state["selected_result"] = None
