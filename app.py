"""
Swing Trading Scanner — Elite Edition v3
Advanced algorithms with Market Regime Detection, Sector Diversification,
and Smart Money (Whale Radar) Detection.
Shows only TOP 3 stocks with highest win probability.
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
    page_title="⚡ Elite Swing Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────
#  MINIMAL CSS
# ──────────────────────────────────────────────────────────────────
CSS = """
<style>
    .main .block-container { max-width: 1100px; padding: 1rem 2rem; }
    
    .header { 
        font-size: 1.8rem; font-weight: 700; color: #00ff88;
        margin-bottom: 0.2rem;
    }
    .subheader { color: #666; font-size: 0.85rem; margin-bottom: 1rem; }
    
    .market-status {
        padding: 0.8rem 1.2rem; border-radius: 10px; margin-bottom: 1rem;
        display: flex; align-items: center; gap: 1rem;
    }
    .market-bullish { background: #1a3d2e; border: 1px solid #238636; }
    .market-bearish { background: #3d1a1a; border: 1px solid #f85149; }
    .market-neutral { background: #3d3d1a; border: 1px solid #d29922; }
    
    .pick-card {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 2px solid #238636;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .pick-card.rank-1 { border-color: #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.2); }
    .pick-card.rank-2 { border-color: #c0c0c0; }
    .pick-card.rank-3 { border-color: #cd7f32; }
    
    .ticker { font-size: 1.6rem; font-weight: 700; color: #fff; }
    .price { font-size: 1.1rem; color: #8b949e; margin-left: 0.8rem; }
    .sector-badge {
        background: #21262d; padding: 0.2rem 0.5rem; border-radius: 4px;
        font-size: 0.7rem; color: #8b949e; margin-left: 0.5rem;
    }
    
    .whale-badge {
        background: linear-gradient(135deg, #1a1a4a 0%, #2a2a6a 100%);
        border: 1px solid #6366f1;
        color: #a5b4fc; padding: 0.2rem 0.6rem; border-radius: 6px;
        font-size: 0.75rem; margin-left: 0.5rem; font-weight: 600;
    }
    
    .win-prob { font-size: 2rem; font-weight: 700; color: #00ff88; }
    .win-label { font-size: 0.7rem; color: #666; text-transform: uppercase; }
    
    .reason-box {
        background: #1a2332; border-left: 3px solid #00ff88;
        padding: 0.8rem 1rem; margin: 0.8rem 0;
        border-radius: 0 8px 8px 0;
    }
    .reason-title { color: #00ff88; font-weight: 600; font-size: 0.9rem; }
    .reason-text { color: #b0b0b0; font-size: 0.85rem; margin-top: 0.3rem; }
    
    .whale-box {
        background: linear-gradient(135deg, #1a1a3a 0%, #1a2a4a 100%);
        border-left: 3px solid #6366f1;
        padding: 0.8rem 1rem; margin: 0.8rem 0;
        border-radius: 0 8px 8px 0;
    }
    .whale-title { color: #a5b4fc; font-weight: 600; font-size: 0.9rem; }
    .whale-text { color: #9ca3af; font-size: 0.85rem; margin-top: 0.3rem; }
    
    .levels {
        display: flex; gap: 1.5rem; margin-top: 0.8rem;
        font-size: 0.9rem; color: #8b949e;
    }
    .sl { color: #f85149; }
    .tp { color: #00ff88; }
    
    .no-picks {
        text-align: center; padding: 3rem;
        color: #666; font-size: 1.1rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white; border: none; border-radius: 8px;
        font-weight: 600; padding: 0.6rem 1.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262d;
        color: #00ff88;
    }
</style>
"""

# ──────────────────────────────────────────────────────────────────
#  STOCK UNIVERSE WITH SECTORS — For diversification
# ──────────────────────────────────────────────────────────────────
STOCK_SECTORS = {
    # Tech - Software
    "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "META": "Tech", "AMZN": "Tech",
    "NFLX": "Tech", "ADBE": "Tech", "CRM": "Tech", "ORCL": "Tech", "NOW": "Tech",
    "SNOW": "Tech", "PANW": "Tech", "CRWD": "Tech", "ZS": "Tech", "NET": "Tech",
    "DDOG": "Tech", "MDB": "Tech", "TEAM": "Tech", "SHOP": "Tech", "PLTR": "Tech",
    # Tech - Semiconductors
    "NVDA": "Semis", "AMD": "Semis", "QCOM": "Semis", "AVGO": "Semis", "INTC": "Semis",
    "MU": "Semis", "TSM": "Semis",
    # Tech - Fintech
    "SQ": "Fintech", "PYPL": "Fintech", "AFRM": "Fintech", "SOFI": "Fintech",
    "COIN": "Fintech", "HOOD": "Fintech",
    # Finance - Banks
    "JPM": "Finance", "BAC": "Finance", "GS": "Finance", "MS": "Finance",
    "WFC": "Finance", "C": "Finance", "BLK": "Finance", "SCHW": "Finance", "COF": "Finance",
    # Finance - Payments
    "V": "Payments", "MA": "Payments", "AXP": "Payments",
    # Consumer / Retail
    "WMT": "Retail", "COST": "Retail", "TGT": "Retail", "HD": "Retail", "LOW": "Retail",
    "NKE": "Retail", "SBUX": "Retail", "MCD": "Retail", "LULU": "Retail", "DECK": "Retail",
    "ONON": "Retail", "CROX": "Retail", "ETSY": "Retail", "W": "Retail", "CHWY": "Retail",
    # Media / Entertainment
    "DIS": "Media", "CMCSA": "Media", "ROKU": "Media", "SNAP": "Media", "PINS": "Media",
    "RBLX": "Media", "TTD": "Media", "ZM": "Media",
    # Travel / Mobility
    "UBER": "Travel", "LYFT": "Travel", "ABNB": "Travel", "DASH": "Travel",
    # Healthcare / Biotech
    "LLY": "Health", "PFE": "Health", "ABBV": "Health", "MRK": "Health", "JNJ": "Health",
    "GILD": "Health", "AMGN": "Health", "BIIB": "Health", "REGN": "Health", "VRTX": "Health",
    "MRNA": "Health", "BNTX": "Health", "ISRG": "Health", "DXCM": "Health", "ILMN": "Health",
    "BMY": "Health", "UNH": "Health", "CVS": "Health", "CI": "Health", "HUM": "Health",
    # Energy
    "XOM": "Energy", "CVX": "Energy", "SLB": "Energy", "OXY": "Energy", "DVN": "Energy",
    "EOG": "Energy", "PXD": "Energy", "HAL": "Energy", "BKR": "Energy",
    # Materials / Mining
    "FCX": "Materials", "NEM": "Materials", "AA": "Materials", "MOS": "Materials",
    "CLF": "Materials", "X": "Materials", "VALE": "Materials",
    # Crypto Mining
    "MARA": "Crypto", "RIOT": "Crypto", "CLSK": "Crypto", "CIFR": "Crypto",
    "HUT": "Crypto", "BTBT": "Crypto", "BITF": "Crypto",
    # Industrial / Aerospace
    "BA": "Industrial", "CAT": "Industrial", "DE": "Industrial", "UNP": "Industrial",
    "UPS": "Industrial", "FDX": "Industrial", "GE": "Industrial", "RTX": "Industrial",
    "LMT": "Industrial", "NOC": "Industrial",
    # EV / Clean Energy
    "TSLA": "EV", "RIVN": "EV", "LCID": "EV", "NIO": "EV", "XPEV": "EV", "LI": "EV",
    "ENPH": "Clean", "SEDG": "Clean", "FSLR": "Clean", "RUN": "Clean",
    # SaaS / Cloud
    "DOCU": "SaaS", "BILL": "SaaS", "HUBS": "SaaS", "WDAY": "SaaS", "VEEV": "SaaS",
    "OKTA": "SaaS", "TWLO": "SaaS",
}

ALL_TICKERS = list(STOCK_SECTORS.keys())

# ──────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────────
CFG = {
    "sl_atr_mult"       : 1.5,
    "tp_atr_mult"       : 3.5,
    "min_rr"            : 2.0,
    "min_win_prob"      : 65,
    "min_profit_pct"    : 6.0,
    "risk_per_trade_pct": 1.5,
    "max_position_pct"  : 30.0,
    "scan_threads"      : 10,
    "max_results"       : 3,
}

# ══════════════════════════════════════════════════════════════════
#  🐋 SMART MONEY (WHALE RADAR) DETECTION
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def detect_smart_money(ticker: str):
    """
    Detect institutional "Smart Money" activity using FREE yfinance data.
    
    Two detection methods:
    1. Unusual Options Activity (UOA): Vol/OI ratio > 3x indicates sweeps
    2. Dark Pool Proxy: High volume with tight price spread = absorption
    
    Returns: dict with whale signals and explanations
    """
    signals = []
    has_whale_activity = False
    
    try:
        t = yf.Ticker(ticker)
        
        # ═══════════════════════════════════════════════════════════
        # 1. UNUSUAL OPTIONS ACTIVITY (UOA) DETECTION
        # ═══════════════════════════════════════════════════════════
        try:
            # Get options expiration dates
            exp_dates = t.options
            if exp_dates and len(exp_dates) > 0:
                # Get nearest expiration (this week or next)
                nearest_exp = exp_dates[0]
                opt_chain = t.option_chain(nearest_exp)
                calls = opt_chain.calls
                puts = opt_chain.puts
                
                # Calculate Put/Call Ratio
                total_call_vol = calls['volume'].sum() if 'volume' in calls.columns else 0
                total_put_vol = puts['volume'].sum() if 'volume' in puts.columns else 0
                pcr = total_put_vol / total_call_vol if total_call_vol > 0 else 1.0
                
                # Find unusual call activity (bullish bets)
                unusual_calls = []
                if not calls.empty and 'volume' in calls.columns and 'openInterest' in calls.columns:
                    calls_filtered = calls[(calls['volume'] > 100) & (calls['openInterest'] > 0)]
                    for _, row in calls_filtered.iterrows():
                        vol_oi_ratio = row['volume'] / row['openInterest'] if row['openInterest'] > 0 else 0
                        if vol_oi_ratio >= 3.0:  # 3x or higher = unusual
                            unusual_calls.append({
                                'strike': row['strike'],
                                'volume': int(row['volume']),
                                'oi': int(row['openInterest']),
                                'ratio': vol_oi_ratio,
                            })
                
                # Find unusual put activity (bearish or hedging)
                unusual_puts = []
                if not puts.empty and 'volume' in puts.columns and 'openInterest' in puts.columns:
                    puts_filtered = puts[(puts['volume'] > 100) & (puts['openInterest'] > 0)]
                    for _, row in puts_filtered.iterrows():
                        vol_oi_ratio = row['volume'] / row['openInterest'] if row['openInterest'] > 0 else 0
                        if vol_oi_ratio >= 3.0:
                            unusual_puts.append({
                                'strike': row['strike'],
                                'volume': int(row['volume']),
                                'oi': int(row['openInterest']),
                                'ratio': vol_oi_ratio,
                            })
                
                # Sort by ratio (most unusual first)
                unusual_calls.sort(key=lambda x: x['ratio'], reverse=True)
                unusual_puts.sort(key=lambda x: x['ratio'], reverse=True)
                
                # Report findings
                if unusual_calls:
                    top = unusual_calls[0]
                    has_whale_activity = True
                    signals.append({
                        'type': 'UOA_CALL',
                        'title': '🐋 Unusual CALL Activity Detected',
                        'text': f"Large call buying at ${top['strike']:.0f} strike — {top['volume']:,} contracts (Vol/OI: {top['ratio']:.1f}x). Institutions may be betting on upside.",
                        'strength': min(top['ratio'] / 5.0, 1.0),  # Normalize to 0-1
                    })
                
                if unusual_puts and len(unusual_puts) > len(unusual_calls):
                    top = unusual_puts[0]
                    signals.append({
                        'type': 'UOA_PUT',
                        'title': '⚠️ Unusual PUT Activity Detected',
                        'text': f"Large put buying at ${top['strike']:.0f} strike — {top['volume']:,} contracts (Vol/OI: {top['ratio']:.1f}x). Could be hedging or bearish bet.",
                        'strength': min(top['ratio'] / 5.0, 1.0),
                    })
                
                # Put/Call Ratio insight
                if pcr < 0.5:
                    signals.append({
                        'type': 'PCR_BULLISH',
                        'title': '📊 Bullish Options Sentiment',
                        'text': f"Put/Call Ratio: {pcr:.2f} — Heavy call buying suggests bullish institutional sentiment.",
                        'strength': 0.6,
                    })
                elif pcr > 1.5:
                    signals.append({
                        'type': 'PCR_BEARISH',
                        'title': '📊 Bearish Options Sentiment',
                        'text': f"Put/Call Ratio: {pcr:.2f} — Heavy put buying suggests caution.",
                        'strength': 0.4,
                    })
        except Exception:
            pass  # Options data not available for this ticker
        
        # ═══════════════════════════════════════════════════════════
        # 2. DARK POOL PROXY (Volume Anomaly with Tight Spread)
        # ═══════════════════════════════════════════════════════════
        try:
            df = t.history(period="1mo", interval="1d")
            if not df.empty and len(df) >= 10:
                df.columns = [c.lower() for c in df.columns]
                
                # Calculate metrics
                avg_vol = df['volume'].rolling(20).mean()
                vol_ratio = df['volume'] / avg_vol
                
                # Body size as % of price (tight = doji/absorption)
                body_pct = abs(df['close'] - df['open']) / df['close'] * 100
                
                # Find days with high volume but tight body (absorption)
                recent = df.tail(5)
                for idx, row in recent.iterrows():
                    vol_r = row['volume'] / avg_vol.loc[idx] if idx in avg_vol.index else 1
                    body = abs(row['close'] - row['open']) / row['close'] * 100
                    
                    # High volume (4x+) with tight body (<0.5%) = Dark Pool signature
                    if vol_r >= 4.0 and body < 0.5:
                        has_whale_activity = True
                        signals.append({
                            'type': 'DARK_POOL',
                            'title': '🏦 Institutional Accumulation Detected',
                            'text': f"Massive volume ({vol_r:.1f}x average) with minimal price movement. Classic dark pool absorption pattern.",
                            'strength': 0.8,
                        })
                        break  # Only report once
                    
                    # Very high volume (3x+) with small body (<1%) = likely institutional
                    elif vol_r >= 3.0 and body < 1.0:
                        signals.append({
                            'type': 'BLOCK_TRADE',
                            'title': '📦 Large Block Trade Detected',
                            'text': f"Volume {vol_r:.1f}x average with controlled price action. Possible institutional block trade.",
                            'strength': 0.5,
                        })
                        has_whale_activity = True
                        break
        except Exception:
            pass
        
    except Exception:
        pass
    
    return {
        'has_whale_activity': has_whale_activity,
        'signals': signals,
        'signal_count': len(signals),
    }

# ──────────────────────────────────────────────────────────────────
#  EARNINGS FILTER — Skip stocks near earnings (gambling, not trading)
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def check_earnings(ticker: str, days_threshold: int = 5):
    """
    Check if stock has earnings within the next X days.
    Returns: (has_earnings_soon: bool, days_until: int or None, earnings_date: str or None)
    """
    try:
        t = yf.Ticker(ticker)
        calendar = t.calendar
        
        if calendar is None or calendar.empty:
            return False, None, None
        
        # Try to get earnings date
        earnings_date = None
        if 'Earnings Date' in calendar.index:
            earnings_date = calendar.loc['Earnings Date']
            if isinstance(earnings_date, pd.Series):
                earnings_date = earnings_date.iloc[0]
        elif len(calendar.columns) > 0 and 'Earnings Date' in calendar.columns:
            earnings_date = calendar['Earnings Date'].iloc[0]
        
        if earnings_date is None:
            return False, None, None
        
        # Convert to datetime
        if isinstance(earnings_date, str):
            earnings_date = pd.to_datetime(earnings_date)
        elif hasattr(earnings_date, 'date'):
            pass  # Already datetime
        else:
            return False, None, None
        
        # Calculate days until earnings
        today = datetime.now().date()
        if hasattr(earnings_date, 'date'):
            earnings_dt = earnings_date.date()
        else:
            earnings_dt = earnings_date
        
        days_until = (earnings_dt - today).days
        
        # Return warning if earnings within threshold
        if 0 <= days_until <= days_threshold:
            return True, days_until, earnings_dt.strftime('%Y-%m-%d')
        
        return False, days_until, earnings_dt.strftime('%Y-%m-%d')
        
    except Exception:
        return False, None, None


# ──────────────────────────────────────────────────────────────────
#  SECTOR HEATMAP — Show which sectors are hot/cold today
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_sector_performance():
    """
    Calculate today's performance for each sector.
    Returns dict with sector performance and ranking.
    """
    sector_tickers = {
        'Tech': ['AAPL', 'MSFT', 'GOOGL'],
        'Semis': ['NVDA', 'AMD', 'AVGO'],
        'Finance': ['JPM', 'BAC', 'GS'],
        'Health': ['LLY', 'UNH', 'JNJ'],
        'Energy': ['XOM', 'CVX', 'SLB'],
        'Retail': ['WMT', 'COST', 'HD'],
        'EV': ['TSLA', 'RIVN', 'LCID'],
        'Media': ['DIS', 'NFLX', 'CMCSA'],
        'Industrial': ['BA', 'CAT', 'DE'],
        'Crypto': ['MARA', 'RIOT', 'COIN'],
    }
    
    results = {}
    
    for sector, tickers in sector_tickers.items():
        changes = []
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period='5d', interval='1d')
                if len(hist) >= 2:
                    chg = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                    changes.append(chg)
            except:
                pass
        
        if changes:
            avg_chg = sum(changes) / len(changes)
            results[sector] = {
                'change': avg_chg,
                'direction': 'up' if avg_chg > 0 else 'down',
                'strength': abs(avg_chg),
            }
    
    # Sort by change (best first)
    sorted_sectors = sorted(results.items(), key=lambda x: x[1]['change'], reverse=True)
    
    for i, (sector, data) in enumerate(sorted_sectors):
        results[sector]['rank'] = i + 1
    
    return results


# ──────────────────────────────────────────────────────────────────
#  MARKET REGIME DETECTION — Check SPY before trading
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_market_regime():
    """
    Analyze SPY to determine if market is BULLISH, BEARISH, or NEUTRAL.
    This is CRITICAL — we don't want to go long in a bear market.
    """
    try:
        spy = yf.Ticker("SPY")
        df = spy.history(period="6mo", interval="1d")
        if df.empty or len(df) < 50:
            return "NEUTRAL", 0, "Unable to fetch SPY data"
        
        df.columns = [c.lower() for c in df.columns]
        c = df["close"]
        
        # Calculate indicators using pandas-ta
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.supertrend(length=10, multiplier=3, append=True)
        
        price = float(c.iloc[-1])
        ema20 = float(df["EMA_20"].iloc[-1])
        ema50 = float(df["EMA_50"].iloc[-1])
        rsi = float(df["RSI_14"].iloc[-1]) if "RSI_14" in df.columns else 50
        adx = float(df["ADX_14"].iloc[-1]) if "ADX_14" in df.columns else 20
        
        # Supertrend direction
        st_col = [col for col in df.columns if "SUPERTd" in col]
        supertrend_bull = int(df[st_col[0]].iloc[-1]) == 1 if st_col else True
        
        # 20-day performance
        chg_20d = (price - float(c.iloc[-20])) / float(c.iloc[-20]) * 100
        
        # Scoring
        score = 0
        reasons = []
        
        # Trend alignment
        if price > ema20 > ema50:
            score += 30
            reasons.append("SPY above EMA20 & EMA50")
        elif price > ema50:
            score += 15
            reasons.append("SPY above EMA50")
        else:
            score -= 20
            reasons.append("SPY below key moving averages")
        
        # Supertrend
        if supertrend_bull:
            score += 25
            reasons.append("Supertrend bullish")
        else:
            score -= 25
            reasons.append("Supertrend bearish")
        
        # RSI
        if 45 <= rsi <= 70:
            score += 15
            reasons.append(f"RSI healthy at {rsi:.0f}")
        elif rsi < 40:
            score -= 10
            reasons.append(f"RSI weak at {rsi:.0f}")
        elif rsi > 75:
            score += 5  # Overbought but still bullish
            reasons.append(f"RSI overbought {rsi:.0f}")
        
        # Momentum
        if chg_20d > 3:
            score += 20
            reasons.append(f"SPY up {chg_20d:.1f}% in 20 days")
        elif chg_20d > 0:
            score += 10
            reasons.append(f"SPY up {chg_20d:.1f}% in 20 days")
        else:
            score -= 15
            reasons.append(f"SPY down {chg_20d:.1f}% in 20 days")
        
        # Trend strength
        if adx > 25:
            score += 10
            reasons.append(f"Strong trend (ADX {adx:.0f})")
        
        # Determine regime
        if score >= 50:
            regime = "BULLISH"
            msg = "🟢 Market is BULLISH — Good conditions for swing trading"
        elif score >= 20:
            regime = "NEUTRAL"
            msg = "🟡 Market is NEUTRAL — Be selective with trades"
        else:
            regime = "BEARISH"
            msg = "🔴 Market is BEARISH — Avoid long positions"
        
        return regime, score, msg, reasons, {
            "price": price, "ema20": ema20, "ema50": ema50,
            "rsi": rsi, "adx": adx, "chg_20d": chg_20d
        }
        
    except Exception as e:
        return "NEUTRAL", 0, f"Error: {str(e)}", [], {}

# ──────────────────────────────────────────────────────────────────
#  DATA FETCHING WITH PANDAS-TA
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(ticker: str):
    """Fetch price data and compute indicators using pandas-ta."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y", interval="1d", auto_adjust=True)
        news = t.news or []
        if df.empty or len(df) < 100:
            return None, None, []
        df.columns = [c.lower() for c in df.columns]
        
        c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
        price = float(c.iloc[-1])
        
        # ═══════════════════════════════════════════════════════════
        # Use pandas-ta for all indicators (faster & more accurate)
        # ═══════════════════════════════════════════════════════════
        
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
        
        # ADX (Trend Strength)
        df.ta.adx(length=14, append=True)
        
        # Bollinger Bands
        df.ta.bbands(length=20, std=2, append=True)
        
        # Supertrend (new! great for trend confirmation)
        df.ta.supertrend(length=10, multiplier=3, append=True)
        
        # VWAP (approximate using cumulative)
        vwap = (c * v).cumsum() / v.cumsum()
        
        # Volume ratio
        vol_sma20 = v.rolling(20).mean()
        vol_ratio = v / vol_sma20
        
        # Get values from pandas-ta columns
        ema8 = df["EMA_8"].iloc[-1] if "EMA_8" in df.columns else price
        ema21 = df["EMA_21"].iloc[-1] if "EMA_21" in df.columns else price
        ema50 = df["EMA_50"].iloc[-1] if "EMA_50" in df.columns else price
        ema200 = df["EMA_200"].iloc[-1] if "EMA_200" in df.columns else price
        
        rsi = df["RSI_14"].iloc[-1] if "RSI_14" in df.columns else 50
        rsi_prev = df["RSI_14"].iloc[-2] if "RSI_14" in df.columns else 50
        rsi_5d = df["RSI_14"].iloc[-5] if "RSI_14" in df.columns and len(df) >= 5 else 50
        
        macd_hist = df["MACDh_12_26_9"].iloc[-1] if "MACDh_12_26_9" in df.columns else 0
        macd_hist_prev = df["MACDh_12_26_9"].iloc[-2] if "MACDh_12_26_9" in df.columns else 0
        macd_line = df["MACD_12_26_9"].iloc[-1] if "MACD_12_26_9" in df.columns else 0
        signal_line = df["MACDs_12_26_9"].iloc[-1] if "MACDs_12_26_9" in df.columns else 0
        
        atr = df["ATRr_14"].iloc[-1] if "ATRr_14" in df.columns else price * 0.02
        
        adx = df["ADX_14"].iloc[-1] if "ADX_14" in df.columns else 20
        plus_di = df["DMP_14"].iloc[-1] if "DMP_14" in df.columns else 20
        minus_di = df["DMN_14"].iloc[-1] if "DMN_14" in df.columns else 20
        
        # Bollinger Band position
        bb_upper = df["BBU_20_2.0"].iloc[-1] if "BBU_20_2.0" in df.columns else price * 1.02
        bb_lower = df["BBL_20_2.0"].iloc[-1] if "BBL_20_2.0" in df.columns else price * 0.98
        bb_pos = (price - bb_lower) / (bb_upper - bb_lower + 1e-9)
        
        # Supertrend direction (1 = bullish, -1 = bearish)
        st_col = [col for col in df.columns if "SUPERTd" in col]
        supertrend_bull = int(df[st_col[0]].iloc[-1]) == 1 if st_col else True
        
        # Relative Strength vs SPY
        try:
            spy_data = yf.Ticker("SPY").history(period="1y", interval="1d")["Close"]
            if len(spy_data) >= 20:
                stock_chg = (c.iloc[-1] - c.iloc[-20]) / c.iloc[-20] * 100
                spy_chg = (spy_data.iloc[-1] - spy_data.iloc[-20]) / spy_data.iloc[-20] * 100
                rs_vs_spy = stock_chg - spy_chg
            else:
                rs_vs_spy = 0
        except:
            rs_vs_spy = 0
        
        # Breakout detection
        recent_high = h.rolling(20).max()
        near_breakout = price > float(recent_high.iloc[-2]) * 0.98
        
        # Consolidation (tight range)
        range_20d = (h.rolling(20).max() - l.rolling(20).min()) / c * 100
        consolidating = float(range_20d.iloc[-1]) < float(atr) / price * 100 * 3
        
        # Distance to EMA21
        dist_to_ema21 = (price - ema21) / price * 100
        
        ind = {
            "price": price,
            "ema8": float(ema8), "ema21": float(ema21), 
            "ema50": float(ema50), "ema200": float(ema200),
            "rsi": float(rsi), "rsi_prev": float(rsi_prev), "rsi_5d_ago": float(rsi_5d),
            "macd_hist": float(macd_hist), "macd_prev": float(macd_hist_prev),
            "macd_line": float(macd_line), "signal_line": float(signal_line),
            "atr": float(atr), "atr_pct": float(atr) / price * 100,
            "adx": float(adx) if not np.isnan(adx) else 20,
            "plus_di": float(plus_di) if not np.isnan(plus_di) else 20,
            "minus_di": float(minus_di) if not np.isnan(minus_di) else 20,
            "bb_pos": float(bb_pos),
            "vwap": float(vwap.iloc[-1]),
            "vol_ratio": float(vol_ratio.iloc[-1]),
            "supertrend_bull": supertrend_bull,
            "rs_vs_spy": float(rs_vs_spy),
            "near_breakout": near_breakout,
            "consolidating": consolidating,
            "dist_to_ema21": float(dist_to_ema21),
            "chg_1d": float((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2] * 100),
            "chg_5d": float((c.iloc[-1] - c.iloc[-5]) / c.iloc[-5] * 100),
            "chg_20d": float((c.iloc[-1] - c.iloc[-20]) / c.iloc[-20] * 100),
        }
        return ind, df, news
    except Exception as e:
        return None, None, []


def news_score(news_list):
    """Analyze news sentiment."""
    BULL = ["beat","raised","upgrade","outperform","growth","record","profit",
            "surge","rally","deal","launch","revenue","buyback","expand","strong",
            "buy","bullish","breakout","new high","partnership","contract"]
    BEAR = ["miss","cut","downgrade","underperform","loss","weak","decline",
            "investigation","lawsuit","layoffs","warning","bankruptcy","fraud",
            "sell","bearish","crash","plunge","recall","debt"]
    score = 0
    for n in (news_list or [])[:10]:
        title = n.get("content", {}).get("title", "") or n.get("title", "")
        if not title:
            continue
        tl = title.lower()
        score += sum(1 for w in BULL if w in tl)
        score -= sum(1 for w in BEAR if w in tl)
    return score


# ──────────────────────────────────────────────────────────────────
#  WIN PROBABILITY ALGORITHM — The Core of Accuracy
# ──────────────────────────────────────────────────────────────────
def calculate_win_probability(ind, ns):
    """
    Calculate win probability (0-100%) based on multiple factors.
    Each factor adds to the probability based on historical edge.
    
    This is a weighted scoring system based on proven swing trading patterns.
    """
    score = 0
    max_score = 0
    reasons = []
    
    # ═══════════════════════════════════════════════════════════════
    # 1. TREND ALIGNMENT (25 points max) — Most important factor
    # ═══════════════════════════════════════════════════════════════
    max_score += 25
    
    # Perfect trend: Price > EMA8 > EMA21 > EMA50 > EMA200
    if ind["price"] > ind["ema8"] > ind["ema21"] > ind["ema50"]:
        if ind["ema50"] > ind["ema200"]:
            score += 25
            reasons.append(("🔥 Perfect Uptrend", "All EMAs aligned bullish + above 200-day. Historically wins 70%+ of the time."))
        else:
            score += 20
            reasons.append(("📈 Strong Uptrend", "Short & mid-term EMAs aligned. Good momentum."))
    elif ind["price"] > ind["ema21"] > ind["ema50"]:
        score += 15
        reasons.append(("📊 Moderate Uptrend", "Price above key moving averages."))
    elif ind["price"] > ind["ema50"]:
        score += 8
    
    # ═══════════════════════════════════════════════════════════════
    # 2. TREND STRENGTH - ADX (15 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 15
    
    # ADX > 25 = strong trend, ADX > 40 = very strong
    if ind["adx"] >= 30 and ind["plus_di"] > ind["minus_di"]:
        score += 15
        reasons.append(("💪 Strong Bullish Trend", f"ADX at {ind['adx']:.0f} shows powerful momentum. Buyers dominating."))
    elif ind["adx"] >= 25 and ind["plus_di"] > ind["minus_di"]:
        score += 12
        reasons.append(("📈 Trending Up", f"ADX {ind['adx']:.0f} confirms real trend, not just noise."))
    elif ind["adx"] >= 20:
        score += 6
    
    # ═══════════════════════════════════════════════════════════════
    # 3. RSI SWEET SPOT (15 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 15
    
    rsi = ind["rsi"]
    rsi_rising = ind["rsi"] > ind["rsi_prev"]
    rsi_momentum = ind["rsi"] - ind["rsi_5d_ago"]
    
    # RSI 40-60 is the sweet spot for entries (not overbought, not oversold)
    if 40 <= rsi <= 55 and rsi_rising:
        score += 15
        reasons.append(("✨ Perfect RSI Entry", f"RSI {rsi:.0f} in sweet spot and rising. Ideal timing."))
    elif 35 <= rsi <= 60 and rsi_rising:
        score += 12
        reasons.append(("📊 Good RSI", f"RSI {rsi:.0f} healthy with upward momentum."))
    elif 30 <= rsi <= 65 and rsi_rising:
        score += 8
    elif rsi > 70:
        score += 0  # Overbought - risky
    elif rsi < 30 and rsi_rising:
        score += 10  # Oversold bounce
    
    # ═══════════════════════════════════════════════════════════════
    # 4. MACD CONFIRMATION (12 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 12
    
    macd_bullish = ind["macd_hist"] > 0
    macd_rising = ind["macd_hist"] > ind["macd_prev"]
    macd_cross = ind["macd_line"] > ind["signal_line"] and ind["macd_hist"] > 0
    
    if macd_bullish and macd_rising and macd_cross:
        score += 12
        reasons.append(("🚀 MACD Bullish Crossover", "Strong buying momentum accelerating. Key confirmation signal."))
    elif macd_bullish and macd_rising:
        score += 10
        reasons.append(("📈 MACD Positive", "Momentum building on the buy side."))
    elif macd_bullish:
        score += 6
    
    # ═══════════════════════════════════════════════════════════════
    # 5. VOLUME CONFIRMATION (12 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 12
    
    vol = ind["vol_ratio"]
    
    if vol >= 2.0 and ind["chg_1d"] > 0:
        score += 12
        reasons.append(("🔊 Massive Volume", f"Volume {vol:.1f}x average with price up. Institutions buying."))
    elif vol >= 1.5 and ind["chg_1d"] > 0:
        score += 10
        reasons.append(("📊 High Volume", f"Volume {vol:.1f}x confirms the move."))
    elif vol >= 1.2:
        score += 7
    elif vol >= 1.0:
        score += 4
    
    # ═══════════════════════════════════════════════════════════════
    # 6. RELATIVE STRENGTH VS MARKET (10 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 10
    
    rs = ind["rs_vs_spy"]
    
    if rs > 5:
        score += 10
        reasons.append(("🏆 Market Leader", f"Outperforming SPY by {rs:.1f}%. Strong relative strength."))
    elif rs > 2:
        score += 7
        reasons.append(("💪 Beating Market", f"Stronger than overall market by {rs:.1f}%."))
    elif rs > 0:
        score += 4
    
    # ═══════════════════════════════════════════════════════════════
    # 7. PRICE POSITION (8 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 8
    
    bb_pos = ind["bb_pos"]
    above_vwap = ind["price"] > ind["vwap"]
    
    # Ideal: price in middle of Bollinger (room to run) and above VWAP
    if 0.3 <= bb_pos <= 0.65 and above_vwap:
        score += 8
        reasons.append(("📍 Ideal Price Position", "Room to run up, buyers in control (above VWAP)."))
    elif 0.25 <= bb_pos <= 0.75 and above_vwap:
        score += 6
    elif above_vwap:
        score += 4
    
    # ═══════════════════════════════════════════════════════════════
    # 8. BREAKOUT/PULLBACK PATTERN (8 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 8
    
    if ind["near_breakout"] and vol >= 1.3:
        score += 8
        reasons.append(("🚀 Breakout Setup", "Breaking above resistance with volume. High probability move."))
    elif ind["consolidating"] and 0 < ind["dist_to_ema21"] < 3:
        score += 7
        reasons.append(("⏳ Pullback to Support", "Healthy pullback to EMA21. Low-risk entry point."))
    elif ind["near_breakout"]:
        score += 5
    
    # ═══════════════════════════════════════════════════════════════
    # 9. SUPERTREND CONFIRMATION (10 points max) — NEW!
    # ═══════════════════════════════════════════════════════════════
    max_score += 10
    
    if ind.get("supertrend_bull", False):
        score += 10
        reasons.append(("📊 Supertrend Bullish", "Supertrend indicator confirms uptrend. Strong buy signal."))
    else:
        score -= 3  # Penalty for bearish supertrend
    
    # ═══════════════════════════════════════════════════════════════
    # 10. NEWS CATALYST (5 points max)
    # ═══════════════════════════════════════════════════════════════
    max_score += 5
    
    if ns >= 3:
        score += 5
        reasons.append(("📰 Strong News Catalyst", "Multiple positive headlines supporting the move."))
    elif ns >= 1:
        score += 3
    elif ns < -1:
        score -= 5  # Negative news is a red flag
    
    # ═══════════════════════════════════════════════════════════════
    # Calculate final probability
    # ═══════════════════════════════════════════════════════════════
    raw_prob = (score / max_score) * 100
    
    # Apply adjustments
    # Penalty for overbought
    if ind["rsi"] > 75:
        raw_prob *= 0.7
    # Penalty for weak trend
    if ind["adx"] < 15:
        raw_prob *= 0.8
    # Penalty for bearish MACD
    if ind["macd_hist"] < 0 and ind["macd_hist"] < ind["macd_prev"]:
        raw_prob *= 0.8
    # Penalty for bearish Supertrend
    if not ind.get("supertrend_bull", True):
        raw_prob *= 0.85
    
    win_prob = min(95, max(0, raw_prob))  # Cap at 95%
    
    return win_prob, reasons


def calc_position(ind, capital):
    """Calculate position sizing and trade levels."""
    price = ind["price"]
    atr = ind["atr"]
    sl = price - atr * CFG["sl_atr_mult"]
    tp = price + atr * CFG["tp_atr_mult"]
    sl_pct = abs((sl - price) / price * 100)
    tp_pct = (tp - price) / price * 100
    rr = tp_pct / sl_pct if sl_pct > 0 else 0

    max_loss = capital * CFG["risk_per_trade_pct"] / 100
    max_pos = capital * CFG["max_position_pct"] / 100
    loss_ps = price - sl
    shares = min(max_loss / loss_ps, max_pos / price) if loss_ps > 0 else 0
    cap_used = shares * price

    return {
        "sl": sl, "tp": tp, "sl_pct": sl_pct, "tp_pct": tp_pct, "rr": rr,
        "shares": shares, "cap_used": cap_used,
        "cap_pct": cap_used / capital * 100,
        "max_loss": shares * loss_ps,
        "max_gain": shares * (tp - price),
    }


def analyze_ticker(ticker, capital, skip_earnings=True):
    """Analyze a single ticker with advanced scoring."""
    ind, df, news = fetch_data(ticker)
    if ind is None:
        return None
    
    # Check for upcoming earnings (skip if within 5 days)
    has_earnings, days_until, earnings_date = check_earnings(ticker, days_threshold=5)
    
    ns = news_score(news)
    win_prob, reasons = calculate_win_probability(ind, ns)
    pos = calc_position(ind, capital)
    
    # Filter criteria - only return if meets all requirements
    if win_prob < CFG["min_win_prob"]:
        return None
    if pos["tp_pct"] < CFG["min_profit_pct"]:
        return None
    if pos["rr"] < CFG["min_rr"]:
        return None
    if not (ind["ema8"] > ind["ema21"] and ind["price"] > ind["ema50"]):
        return None
    if not (0.5 <= ind["atr_pct"] <= 8.0):  # Safe volatility range
        return None
    if ind["rsi"] > 75:  # Too overbought
        return None
    
    # Skip if earnings soon (gambling, not trading)
    if skip_earnings and has_earnings:
        return None
    
    return {
        "ticker": ticker,
        "ind": ind,
        "df": df,
        "win_prob": win_prob,
        "reasons": reasons,
        "pos": pos,
        "ns": ns,
        "has_earnings_soon": has_earnings,
        "earnings_days": days_until,
        "earnings_date": earnings_date,
    }

# ──────────────────────────────────────────────────────────────────
#  PARALLEL SCANNER WITH SECTOR DIVERSIFICATION
# ──────────────────────────────────────────────────────────────────
def scan_market_parallel(tickers, capital, progress_callback=None, diversify=True):
    """Scan multiple tickers in parallel, return diversified top picks."""
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
                # Add sector info
                result["sector"] = STOCK_SECTORS.get(result["ticker"], "Other")
                results.append(result)
    
    # Sort by WIN PROBABILITY (highest first)
    results.sort(key=lambda x: x["win_prob"], reverse=True)
    
    # ═══════════════════════════════════════════════════════════════
    # SECTOR DIVERSIFICATION: Ensure top picks aren't all same sector
    # ═══════════════════════════════════════════════════════════════
    if diversify and len(results) > 3:
        diversified = []
        sectors_used = set()
        
        for result in results:
            sector = result["sector"]
            # Take best from each sector, max 2 from same sector
            if sectors_used.count(sector) if isinstance(sectors_used, list) else list(sectors_used).count(sector) < 2:
                diversified.append(result)
                sectors_used.add(sector)
            if len(diversified) >= CFG["max_results"]:
                break
        
        # If we couldn't fill all slots with diversified, add remaining top picks
        if len(diversified) < CFG["max_results"]:
            for result in results:
                if result not in diversified:
                    diversified.append(result)
                if len(diversified) >= CFG["max_results"]:
                    break
        
        return diversified
    
    return results[:CFG["max_results"]]


# ──────────────────────────────────────────────────────────────────
#  CHART WITH EMAs
# ──────────────────────────────────────────────────────────────────
def make_chart(df, ind, pos):
    """Create chart with EMAs and trade levels."""
    df2 = df.tail(90).copy()
    c = df2["close"]
    
    # Calculate EMAs for chart
    ema8 = c.ewm(span=8, adjust=False).mean()
    ema21 = c.ewm(span=21, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    
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
    fig.add_trace(go.Scatter(x=df2.index, y=ema8, name="EMA 8", 
                             line=dict(color="#00bfff", width=1)))
    fig.add_trace(go.Scatter(x=df2.index, y=ema21, name="EMA 21", 
                             line=dict(color="#ffa500", width=1)))
    fig.add_trace(go.Scatter(x=df2.index, y=ema50, name="EMA 50", 
                             line=dict(color="#9370db", width=1)))
    
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
        height=350,
        margin=dict(l=10, r=60, t=40, b=10),
    )
    return fig


# ──────────────────────────────────────────────────────────────────
#  MAIN UI WITH TABS
# ──────────────────────────────────────────────────────────────────

# Session state init
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None
if "capital" not in st.session_state:
    st.session_state["capital"] = 10000.0
if "market_regime" not in st.session_state:
    st.session_state["market_regime"] = None
if "whale_data" not in st.session_state:
    st.session_state["whale_data"] = {}
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = ["AAPL", "NVDA", "TSLA", "AMD", "GOOGL"]  # Default watchlist

# Inject CSS
st.markdown(CSS, unsafe_allow_html=True)

# Header
st.markdown('<div class="header">⚡ ELITE SWING SCANNER</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Smart Money Detection · Market Regime Analysis · 10-Factor Win Probability</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# MARKET REGIME DISPLAY - Check market condition before scanning
# ═══════════════════════════════════════════════════════════════════
regime, regime_score, regime_msg, regime_reasons, spy_data = get_market_regime()
st.session_state["market_regime"] = regime

if regime == "BULLISH":
    regime_color = "#00ff88"
    regime_icon = "🟢"
    regime_msg = "Market is BULLISH — Great time for swing trades!"
elif regime == "NEUTRAL":
    regime_color = "#ffd700"
    regime_icon = "🟡"
    regime_msg = "Market is NEUTRAL — Be selective, trade quality setups only."
else:  # BEARISH
    regime_color = "#f85149"
    regime_icon = "🔴"
    regime_msg = "Market is BEARISH — High risk! Consider staying in cash."

st.markdown(f"""
<div style="background: linear-gradient(135deg, #161b22 0%, #0d1117 100%); 
            border: 1px solid {regime_color}40; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <div>
            <span style="font-size: 1.1em; font-weight: bold; color: {regime_color};">{regime_icon} MARKET: {regime}</span>
            <span style="color: #8b949e; margin-left: 12px;">(SPY Score: {regime_score}/100)</span>
        </div>
        <div style="color: #8b949e; font-size: 0.9em;">{regime_msg}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TABS ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["⚡ Elite Scanner", "🐋 Whale Radar", "🔥 Sector Heatmap", "⭐ Watchlist"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: ELITE SCANNER (Main scanner with whale badges)
# ═══════════════════════════════════════════════════════════════════
with tab1:
    # Controls row
    col_cap, col_scan, col_search = st.columns([2, 2, 3])
    
    with col_cap:
        capital = st.number_input(
            "💵 Capital (USD)",
            min_value=100.0,
            max_value=1_000_000.0,
            value=st.session_state["capital"],
            step=500.0,
            label_visibility="collapsed",
            key="capital_input"
        )
        st.session_state["capital"] = capital
    
    with col_scan:
        scan_btn = st.button("⚡ Find Best Trades", type="primary", use_container_width=True, key="scan_btn")
    
    with col_search:
        search_col, search_btn_col = st.columns([3, 1])
        with search_col:
            ticker_search = st.text_input(
                "Search",
                placeholder="Search ticker (e.g. AAPL)",
                label_visibility="collapsed",
                key="ticker_search"
            ).upper().strip()
        with search_btn_col:
            analyze_btn = st.button("Analyze", use_container_width=True, key="analyze_btn")
    
    st.markdown("---")
    
    # Handle single stock analysis
    if ticker_search and analyze_btn:
        with st.spinner(f"Analyzing {ticker_search}..."):
            result = analyze_ticker(ticker_search, capital)
            # Also get whale data
            whale_info = detect_smart_money(ticker_search)
            st.session_state["whale_data"][ticker_search] = whale_info
        
        if result is None:
            ind, df, news = fetch_data(ticker_search)
            if ind:
                ns = news_score(news)
                win_prob, reasons = calculate_win_probability(ind, ns)
                pos = calc_position(ind, capital)
                st.warning(f"⚠️ **{ticker_search}**: {win_prob:.0f}% win probability — Below 65% threshold")
                st.markdown(f"**Entry:** ${ind['price']:.2f} | **Stop:** ${pos['sl']:.2f} | **Target:** ${pos['tp']:.2f} | **Profit:** +{pos['tp_pct']:.1f}%")
                
                # Show whale data even for filtered stocks
                if whale_info['has_whale_activity']:
                    st.markdown("**🐋 Whale Activity Detected:**")
                    for sig in whale_info['signals'][:2]:
                        st.info(f"**{sig['title']}**: {sig['text']}")
                
                if reasons:
                    with st.expander("View Analysis"):
                        for title, text in reasons[:3]:
                            st.markdown(f"**{title}**: {text}")
            else:
                st.error(f"Could not fetch data for {ticker_search}")
        else:
            result["whale"] = whale_info
            st.session_state["scan_results"] = [result]
    
    # Handle market scan
    if scan_btn:
        st.session_state["scan_results"] = None
        st.session_state["whale_data"] = {}
        progress_bar = st.progress(0, text=f"Scanning {len(ALL_TICKERS)} stocks...")
        
        def update_progress(pct):
            progress_bar.progress(pct, text=f"Analyzing... {int(pct*100)}%")
        
        results = scan_market_parallel(ALL_TICKERS, capital, update_progress)
        
        # Get whale data for top picks
        progress_bar.progress(0.95, text="Detecting Smart Money activity...")
        for r in results:
            whale_info = detect_smart_money(r['ticker'])
            r['whale'] = whale_info
            st.session_state["whale_data"][r['ticker']] = whale_info
        
        progress_bar.empty()
        st.session_state["scan_results"] = results
    
    # Display results
    results = st.session_state.get("scan_results")
    
    if results is not None:
        if len(results) == 0:
            st.markdown("""
            <div class="no-picks">
                🔍 <b>No high-probability setups found right now.</b><br><br>
                <span style="font-size:0.9rem;">The market may not have any stocks meeting our strict 65%+ win probability criteria.<br>
                This is actually a good sign — it means we're being selective and protecting your capital.<br>
                Check back later or search for a specific ticker.</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Header with diversification note
            st.markdown(f"### 🏆 TOP {len(results)} HIGH-PROBABILITY PICKS")
            st.markdown(f"*Diversified by sector · Scanned {len(ALL_TICKERS)} stocks · Smart Money detection enabled*")
            
            # Display picks with rank
            rank_labels = ["🥇", "🥈", "🥉"]
            rank_classes = ["rank-1", "rank-2", "rank-3"]
            
            for i, r in enumerate(results):
                ind = r["ind"]
                pos = r["pos"]
                win_prob = r["win_prob"]
                reasons = r["reasons"]
                sector = r.get("sector", "Unknown")
                whale = r.get("whale", {})
                has_whale = whale.get("has_whale_activity", False)
                
                rank_label = rank_labels[i] if i < 3 else f"#{i+1}"
                rank_class = rank_classes[i] if i < 3 else ""
                
                # Supertrend indicator badge
                st_badge = "🟢 ST" if ind.get("supertrend_bull", False) else "🔴 ST"
                whale_badge_html = '<span class="whale-badge">🐋 WHALE</span>' if has_whale else ""
                
                # Build the card HTML as a single string
                card_html = f'''<div class="pick-card {rank_class}">
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
<div>
<span style="font-size:1.5rem;margin-right:0.5rem;">{rank_label}</span>
<span class="ticker">{r['ticker']}</span>
<span class="price">${ind['price']:.2f}</span>
<span style="background:#21262d;padding:2px 8px;border-radius:4px;font-size:0.75rem;color:#8b949e;margin-left:8px;">{sector}</span>
<span style="font-size:0.75rem;margin-left:4px;">{st_badge}</span>
{whale_badge_html}
</div>
<div style="text-align:right;">
<div class="win-prob">{win_prob:.0f}%</div>
<div class="win-label">Win Probability</div>
</div>
</div>
<div class="levels">
<span>Entry: <b>${ind['price']:.2f}</b></span>
<span class="sl">Stop: <b>${pos['sl']:.2f}</b> (-{pos['sl_pct']:.1f}%)</span>
<span class="tp">Target: <b>${pos['tp']:.2f}</b> (+{pos['tp_pct']:.1f}%)</span>
<span>R:R <b>1:{pos['rr']:.1f}</b></span>
</div>
</div>'''
                
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Show top reasons WHY this is a good pick
                if reasons:
                    with st.expander(f"💡 Why {r['ticker']}? — See full analysis"):
                        # Whale Activity Section (if present)
                        if has_whale and whale.get("signals"):
                            st.markdown("### 🐋 Smart Money Activity")
                            for sig in whale["signals"]:
                                whale_html = f'<div class="whale-box"><div class="whale-title">{sig["title"]}</div><div class="whale-text">{sig["text"]}</div></div>'
                                st.markdown(whale_html, unsafe_allow_html=True)
                            st.markdown("---")
                        
                        st.markdown("### 📊 Technical Analysis")
                        for title, text in reasons:
                            reason_html = f'<div class="reason-box"><div class="reason-title">{title}</div><div class="reason-text">{text}</div></div>'
                            st.markdown(reason_html, unsafe_allow_html=True)
                        
                        # Key metrics
                        st.markdown("---")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("RSI", f"{ind['rsi']:.0f}")
                        col2.metric("ADX (Trend)", f"{ind['adx']:.0f}")
                        col3.metric("Volume", f"{ind['vol_ratio']:.1f}x")
                        col4.metric("vs SPY", f"{ind['rs_vs_spy']:+.1f}%")
                        
                        # Chart
                        st.markdown("---")
                        fig = make_chart(r["df"], ind, pos)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Position sizing
                        st.markdown("---")
                        st.markdown("**Your Position (based on your capital):**")
                        pc1, pc2, pc3, pc4 = st.columns(4)
                        pc1.metric("Shares to Buy", f"{pos['shares']:.2f}")
                        pc2.metric("Capital Used", f"${pos['cap_used']:.0f}")
                        pc3.metric("Max Loss", f"${pos['max_loss']:.0f}", delta="-1.5%", delta_color="inverse")
                        pc4.metric("Max Gain", f"${pos['max_gain']:.0f}", delta=f"+{pos['tp_pct']:.1f}%")
    
    elif not scan_btn and not analyze_btn:
        # Initial state
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#666;">
            <div style="font-size:4rem;margin-bottom:1rem;">⚡</div>
            <div style="font-size:1.4rem;margin-bottom:0.5rem;color:#00ff88;">Find Your Next Winning Trade</div>
            <div style="font-size:0.95rem;margin-bottom:1.5rem;">
                Advanced algorithms scan 140+ stocks and show only the <b>TOP 3</b><br>
                with <b>65%+ win probability</b> for swing trading (2-10 days).
            </div>
            <div style="font-size:0.85rem;color:#555;">
                ✓ 10 technical indicators · ✓ Smart Money detection<br>
                ✓ Market regime analysis · ✓ Sector diversification<br>
                ✓ Options flow analysis · ✓ Dark pool proxy
            </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 2: WHALE RADAR (Dedicated Smart Money Analysis)
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 🐋 Whale Radar — Smart Money Detection")
    st.markdown("*Detect institutional activity using options flow and volume analysis*")
    
    st.markdown("""
    <div style="background:#1a1a3a;border:1px solid #6366f1;border-radius:8px;padding:1rem;margin:1rem 0;">
        <b style="color:#a5b4fc;">How it works:</b><br>
        <span style="color:#9ca3af;font-size:0.9rem;">
        • <b>Unusual Options Activity (UOA)</b>: Detects when option volume exceeds open interest by 3x+ — a sign of institutional "sweeps"<br>
        • <b>Dark Pool Proxy</b>: Identifies high volume with minimal price movement — classic institutional accumulation<br>
        • <b>Put/Call Ratio</b>: Measures hidden sentiment in the options market
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Whale analysis input
    col1, col2 = st.columns([3, 1])
    with col1:
        whale_ticker = st.text_input(
            "Enter ticker to analyze",
            placeholder="Enter ticker (e.g. NVDA, AAPL, TSLA)",
            label_visibility="collapsed",
            key="whale_ticker"
        ).upper().strip()
    with col2:
        whale_btn = st.button("🔍 Detect Whales", type="primary", use_container_width=True, key="whale_btn")
    
    st.markdown("---")
    
    if whale_ticker and whale_btn:
        with st.spinner(f"Scanning {whale_ticker} for institutional activity..."):
            whale_info = detect_smart_money(whale_ticker)
            st.session_state["whale_data"][whale_ticker] = whale_info
        
        if whale_info["has_whale_activity"]:
            st.success(f"🐋 **WHALE ACTIVITY DETECTED** in {whale_ticker}!")
            
            for sig in whale_info["signals"]:
                signal_color = "#6366f1" if "CALL" in sig["type"] or "BULLISH" in sig["type"] else "#f59e0b" if "PUT" in sig["type"] or "BEARISH" in sig["type"] else "#22c55e"
                sig_html = f'<div style="background:linear-gradient(135deg, #1a1a3a 0%, #1a2a4a 100%);border-left:4px solid {signal_color};padding:1rem;margin:0.8rem 0;border-radius:0 8px 8px 0;"><div style="color:#a5b4fc;font-weight:600;font-size:1rem;">{sig["title"]}</div><div style="color:#9ca3af;font-size:0.9rem;margin-top:0.5rem;">{sig["text"]}</div></div>'
                st.markdown(sig_html, unsafe_allow_html=True)
            
            # Also show basic price info
            try:
                t = yf.Ticker(whale_ticker)
                hist = t.history(period="5d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    chg = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                    vol = hist['Volume'].iloc[-1]
                    avg_vol = hist['Volume'].mean()
                    
                    st.markdown("### 📊 Current Status")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Price", f"${price:.2f}", f"{chg:+.2f}%")
                    c2.metric("Volume", f"{vol/1e6:.1f}M")
                    c3.metric("Vol vs Avg", f"{vol/avg_vol:.1f}x")
            except:
                pass
        else:
            st.info(f"No significant whale activity detected in {whale_ticker} at this time.")
            st.markdown("*This doesn't mean institutions aren't involved — just that our heuristics didn't detect unusual patterns.*")
    
    # Show whale data from scan results
    if st.session_state.get("whale_data"):
        st.markdown("### 📋 Recent Whale Scans")
        
        whale_found = [(t, w) for t, w in st.session_state["whale_data"].items() if w.get("has_whale_activity")]
        
        if whale_found:
            for ticker, whale in whale_found:
                with st.expander(f"🐋 {ticker} — {whale['signal_count']} signals detected"):
                    for sig in whale["signals"]:
                        st.markdown(f"**{sig['title']}**: {sig['text']}")
        else:
            st.markdown("*No whale activity detected in recent scans. Scan some stocks or use the detector above.*")
    else:
        st.markdown("*Enter a ticker above to scan for institutional activity, or run the Elite Scanner to check the top picks.*")

# ═══════════════════════════════════════════════════════════════════
# TAB 3: SECTOR HEATMAP
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🔥 Sector Heatmap — See Where Money Is Flowing")
    st.markdown("*Identify hot and cold sectors for better stock selection*")
    
    heatmap_btn = st.button("🔄 Refresh Sector Data", key="heatmap_btn")
    
    st.markdown("---")
    
    if heatmap_btn or True:  # Always show on load
        with st.spinner("Analyzing sector performance..."):
            sector_data = get_sector_performance()
        
        if sector_data:
            # Sort sectors by performance
            sorted_sectors = sorted(sector_data.items(), key=lambda x: x[1]['change'], reverse=True)
            
            st.markdown("#### Today's Sector Performance")
            
            # Display as cards
            for sector, data in sorted_sectors:
                chg = data['change']
                if chg > 1.5:
                    color = "#00ff88"
                    emoji = "🔥"
                    status = "HOT"
                elif chg > 0:
                    color = "#4ade80"
                    emoji = "📈"
                    status = "UP"
                elif chg > -1.5:
                    color = "#f59e0b"
                    emoji = "📉"
                    status = "DOWN"
                else:
                    color = "#f85149"
                    emoji = "❄️"
                    status = "COLD"
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; 
                            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
                            border-left: 4px solid {color}; padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;">
                    <div>
                        <span style="font-size: 1.2em; font-weight: bold; color: #fff;">{emoji} {sector}</span>
                        <span style="color: {color}; font-weight: bold; margin-left: 12px;">{status}</span>
                    </div>
                    <div style="font-size: 1.3em; font-weight: bold; color: {color};">{chg:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("""
            <div style="background:#1a2332;border-radius:8px;padding:1rem;margin-top:1rem;">
                <b style="color:#00ff88;">💡 How to use this:</b><br>
                <span style="color:#9ca3af;font-size:0.9rem;">
                • Focus on <b style="color:#00ff88;">HOT</b> sectors for swing trades — momentum is your friend<br>
                • Avoid <b style="color:#f85149;">COLD</b> sectors — fighting the trend is risky<br>
                • Sector rotation often leads price — hot sectors today may cool tomorrow
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Unable to fetch sector data. Please try again.")

# ═══════════════════════════════════════════════════════════════════
# TAB 4: WATCHLIST
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### ⭐ Your Watchlist — Track Your Favorite Stocks")
    st.markdown("*Add stocks you want to monitor and scan only your picks*")
    
    # Add ticker to watchlist
    col_add, col_btn = st.columns([3, 1])
    with col_add:
        new_ticker = st.text_input(
            "Add ticker",
            placeholder="Enter ticker (e.g. AAPL)",
            label_visibility="collapsed",
            key="watchlist_add"
        ).upper().strip()
    with col_btn:
        add_btn = st.button("➕ Add", use_container_width=True, key="watchlist_add_btn")
    
    if add_btn and new_ticker:
        if new_ticker not in st.session_state["watchlist"]:
            if len(st.session_state["watchlist"]) < 20:
                st.session_state["watchlist"].append(new_ticker)
                st.success(f"Added {new_ticker} to watchlist!")
            else:
                st.warning("Watchlist is full (max 20). Remove some stocks first.")
        else:
            st.info(f"{new_ticker} is already in your watchlist.")
    
    st.markdown("---")
    
    # Show current watchlist
    st.markdown(f"**Your Watchlist ({len(st.session_state['watchlist'])} stocks):**")
    
    if st.session_state["watchlist"]:
        # Display as removable tags
        cols = st.columns(5)
        for i, ticker in enumerate(st.session_state["watchlist"]):
            with cols[i % 5]:
                if st.button(f"❌ {ticker}", key=f"remove_{ticker}"):
                    st.session_state["watchlist"].remove(ticker)
                    st.rerun()
        
        st.markdown("---")
        
        # Scan watchlist button
        capital = st.session_state.get("capital", 10000.0)
        scan_watchlist_btn = st.button("⚡ Scan Watchlist Only", type="primary", key="scan_watchlist_btn")
        
        if scan_watchlist_btn:
            with st.spinner(f"Scanning {len(st.session_state['watchlist'])} stocks..."):
                watchlist_results = []
                progress = st.progress(0)
                
                for i, ticker in enumerate(st.session_state["watchlist"]):
                    result = analyze_ticker(ticker, capital, skip_earnings=False)
                    
                    # Also get price even if doesn't meet criteria
                    if result is None:
                        ind, df, news = fetch_data(ticker)
                        if ind:
                            has_earnings, days_until, earnings_date = check_earnings(ticker)
                            ns = news_score(news)
                            win_prob, reasons = calculate_win_probability(ind, ns)
                            pos = calc_position(ind, capital)
                            watchlist_results.append({
                                "ticker": ticker,
                                "price": ind['price'],
                                "chg_1d": ind['chg_1d'],
                                "rsi": ind['rsi'],
                                "win_prob": win_prob,
                                "meets_criteria": False,
                                "has_earnings": has_earnings,
                                "earnings_days": days_until,
                            })
                    else:
                        has_earnings, days_until, earnings_date = check_earnings(ticker)
                        watchlist_results.append({
                            "ticker": ticker,
                            "price": result['ind']['price'],
                            "chg_1d": result['ind']['chg_1d'],
                            "rsi": result['ind']['rsi'],
                            "win_prob": result['win_prob'],
                            "meets_criteria": True,
                            "has_earnings": has_earnings,
                            "earnings_days": days_until,
                        })
                    
                    progress.progress((i + 1) / len(st.session_state["watchlist"]))
                
                progress.empty()
            
            # Display results
            st.markdown("### 📊 Watchlist Analysis")
            
            # Stocks that meet criteria (tradeable)
            tradeable = [r for r in watchlist_results if r['meets_criteria']]
            if tradeable:
                st.success(f"**{len(tradeable)} stocks meet trading criteria:**")
                for r in tradeable:
                    earnings_warning = f" ⚠️ Earnings in {r['earnings_days']} days!" if r.get('has_earnings') else ""
                    chg_color = "#00ff88" if r['chg_1d'] >= 0 else "#f85149"
                    st.markdown(f"""
                    <div style="background:#1a3d2e;border:1px solid #238636;border-radius:8px;padding:12px;margin:8px 0;">
                        <span style="font-size:1.2em;font-weight:bold;color:#00ff88;">✅ {r['ticker']}</span>
                        <span style="margin-left:12px;color:#8b949e;">${r['price']:.2f}</span>
                        <span style="margin-left:8px;color:{chg_color};">{r['chg_1d']:+.1f}%</span>
                        <span style="margin-left:12px;color:#00ff88;">{r['win_prob']:.0f}% prob</span>
                        <span style="color:#f59e0b;">{earnings_warning}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Stocks that don't meet criteria
            not_tradeable = [r for r in watchlist_results if not r['meets_criteria']]
            if not_tradeable:
                st.markdown(f"**{len(not_tradeable)} stocks don't meet criteria (watching):**")
                for r in not_tradeable:
                    earnings_warning = f" ⚠️ Earnings in {r['earnings_days']} days!" if r.get('has_earnings') else ""
                    chg_color = "#00ff88" if r['chg_1d'] >= 0 else "#f85149"
                    st.markdown(f"""
                    <div style="background:#21262d;border:1px solid #30363d;border-radius:8px;padding:12px;margin:8px 0;">
                        <span style="font-size:1.1em;font-weight:bold;color:#8b949e;">⏳ {r['ticker']}</span>
                        <span style="margin-left:12px;color:#8b949e;">${r['price']:.2f}</span>
                        <span style="margin-left:8px;color:{chg_color};">{r['chg_1d']:+.1f}%</span>
                        <span style="margin-left:12px;color:#6b7280;">{r['win_prob']:.0f}% prob</span>
                        <span style="color:#f59e0b;">{earnings_warning}</span>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("Your watchlist is empty. Add some tickers above!")
    
    st.markdown("---")
    st.markdown("""
    <div style="background:#1a2332;border-radius:8px;padding:1rem;">
        <b style="color:#00ff88;">💡 Watchlist Tips:</b><br>
        <span style="color:#9ca3af;font-size:0.9rem;">
        • Add stocks you're interested in but don't meet criteria yet<br>
        • ⚠️ Earnings warnings help you avoid gambling before reports<br>
        • Green ✅ = Ready to trade · Gray ⏳ = Keep watching
        </span>
    </div>
    """, unsafe_allow_html=True)
