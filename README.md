# ⚡ Elite Swing Scanner

A professional-grade US stock market scanner for swing trading. Features **Smart Money (Whale) Detection**, **10-factor Win Probability Algorithm**, and **Market Regime Analysis**.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

---

## 🎯 What It Does

- **Scans 142 stocks** across 16 sectors (Tech, Semis, Finance, Energy, etc.)
- **10-factor scoring system** calculates Win Probability (0-100%)
- **Only shows TOP 3 picks** with 65%+ probability — no noise
- **🐋 Whale Radar** — Detects institutional "Smart Money" activity
- **Market Regime Detection** — checks if SPY is bullish before trading
- **Sector Diversification** — ensures picks aren't all from same sector
- **Clear explanations** — tells you WHY each stock is a good pick

---

## 🐋 NEW: Smart Money (Whale Radar) Detection

Detect institutional activity using FREE data — no expensive Bloomberg terminal needed!

### Unusual Options Activity (UOA)
- Scans options chains for contracts where **Volume > 3x Open Interest**
- This is a strong proxy for institutional "sweeps" (large directional bets)
- Calculates **Put/Call Ratio** to gauge hidden sentiment

### Dark Pool Proxy
- Detects high volume spikes (4x+ average) with **tight price spreads**
- This pattern indicates institutional "absorption" — buying without moving price
- Classic signature of dark pool / block trade activity

### How It Appears
- **🐋 WHALE badge** on stocks with detected activity
- Detailed breakdown showing exact options contracts and volume ratios
- Dedicated "Whale Radar" tab for deep analysis on any ticker

---

## 🧠 Win Probability Algorithm (10 Factors)

| Factor | Max Points | What It Checks |
|--------|------------|----------------|
| 1. Trend Alignment | 25 | EMA8 > EMA21 > EMA50 > EMA200 |
| 2. ADX Trend Strength | 15 | ADX > 25 with +DI dominating |
| 3. RSI Sweet Spot | 15 | RSI 40-55 and rising |
| 4. MACD Confirmation | 12 | Bullish crossover, histogram rising |
| 5. Volume Confirmation | 12 | 1.5x+ average volume on up day |
| 6. Relative Strength | 10 | Outperforming SPY over 20 days |
| 7. Price Position | 8 | Middle of Bollinger, above VWAP |
| 8. Breakout/Pullback | 8 | Near resistance or EMA21 pullback |
| 9. Supertrend | 10 | Supertrend indicator bullish |
| 10. News Catalyst | 5 | Positive headlines |

**Total: 120 points max → Converted to 0-100% probability**

---

## 📊 Market Regime Detection

Before showing any picks, the scanner analyzes **SPY (S&P 500)** to determine market conditions:

- 🟢 **BULLISH** (Score ≥50): Great conditions for swing trades
- 🟡 **NEUTRAL** (Score 20-49): Be selective, trade quality only
- 🔴 **BEARISH** (Score <20): Avoid long positions

---

## 🛡️ Risk Management

Professional risk rules built-in:

- **Max 1.5% risk** per trade (protects capital)
- **Max 30% allocation** to any single stock
- **Stop Loss**: 1.5x ATR below entry
- **Take Profit**: 3.5x ATR above entry
- **Minimum R:R**: 1:2 required

---

## 📱 Two-Tab Interface

| Tab | Purpose |
|-----|---------|
| **⚡ Elite Scanner** | Main scanner with technical analysis + whale badges |
| **🐋 Whale Radar** | Dedicated Smart Money detection for any ticker |

---

## ⚡ Technical Features

- **Parallel scanning** — 10 threads for fast analysis
- **pandas-ta integration** — 130+ professional indicators
- **Supertrend indicator** — Powerful trend confirmation
- **Options chain analysis** — Vol/OI ratio detection
- **Real-time data** — Via yfinance API (free)

---

## 🚀 Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or install manually:
```bash
pip install streamlit yfinance pandas numpy plotly requests pandas-ta
streamlit run app.py
```

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Fork this repository to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app**
4. Select this repo, set main file to `app.py`
5. Click **Deploy**

Live in ~2 minutes!

---

## 📁 Project Structure

```
swing-scanner/
├── app.py              # Main application (all-in-one)
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

---

## 📈 Stocks Covered (142 Total)

**Tech**: AAPL, MSFT, GOOGL, META, AMZN, NFLX, CRM, ADBE, ORCL  
**Semiconductors**: NVDA, AMD, AVGO, QCOM, MU, TSM  
**Finance**: JPM, BAC, WFC, GS, MS, C, BLK  
**Payments**: V, MA, PYPL, SQ  
**Retail**: WMT, COST, TGT, HD, LOW, NKE, SBUX, MCD  
**Health**: UNH, JNJ, PFE, ABBV, MRK, LLY, MRNA  
**Energy**: XOM, CVX, COP, SLB, OXY  
**EV**: TSLA, RIVN, LCID, NIO  
**And more...**

---

## ⚠️ Disclaimer

**This tool is for educational and informational purposes only.**

- Not financial advice
- Past performance doesn't guarantee future results
- Smart Money detection is heuristic-based, not 100% accurate
- Always do your own research
- Never invest more than you can afford to lose

---

## 📜 License

MIT License - Free to use and modify.
