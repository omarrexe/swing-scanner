#!/usr/bin/env python3
"""
🤖 Elite Swing Trading Bot v2
Self-contained bot: Scans + Trades + Alerts

Features:
- Same 142 stocks as app.py
- 10-factor win probability algorithm
- Full money management ($100K account)
- Position limits & daily loss protection
- Telegram alerts for everything

Usage:
    python bot_v2.py              # Run once
    python bot_v2.py --loop       # Run continuously (every 30 min)
"""

import sys
import time
import logging
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz
import requests

# ══════════════════════════════════════════════════════════════════
# SETUP LOGGING
# ══════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# LOAD CONFIGURATION
# ══════════════════════════════════════════════════════════════════
try:
    from config import (
        ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL,
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DISPLAY_TIMEZONE
    )
except ImportError:
    logger.error("config.py not found!")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════
# MONEY MANAGEMENT SETTINGS
# ══════════════════════════════════════════════════════════════════
CAPITAL = 100000              # Starting capital
RISK_PER_TRADE_PCT = 1.5      # Max 1.5% risk per trade ($1,500)
MAX_POSITION_PCT = 10.0       # Max 10% per position ($10,000)
MAX_OPEN_POSITIONS = 5        # Max 5 positions at once
DAILY_LOSS_LIMIT_PCT = 3.0    # Stop trading if down 3% today ($3,000)
MIN_WIN_PROB = 65             # Only trade 65%+ probability
MIN_REWARD_RISK = 2.0         # Minimum 2:1 reward/risk
MIN_TARGET_PCT = 5.0          # Minimum 5% upside target

# ══════════════════════════════════════════════════════════════════
# STOCK UNIVERSE (142 stocks from app.py)
# ══════════════════════════════════════════════════════════════════
STOCK_SECTORS = {
    # Tech Giants
    "AAPL": "Tech", "MSFT": "Tech", "GOOGL": "Tech", "META": "Tech", "AMZN": "Tech",
    # Semiconductors
    "NVDA": "Semis", "AMD": "Semis", "AVGO": "Semis", "QCOM": "Semis", "INTC": "Semis",
    "MU": "Semis", "AMAT": "Semis", "LRCX": "Semis", "KLAC": "Semis", "MRVL": "Semis",
    "TSM": "Semis", "ASML": "Semis", "ARM": "Semis", "SMCI": "Semis",
    # EV & Auto
    "TSLA": "EV", "RIVN": "EV", "LCID": "EV", "F": "EV", "GM": "EV", "LI": "EV", "NIO": "EV", "XPEV": "EV",
    # Finance
    "JPM": "Finance", "BAC": "Finance", "GS": "Finance", "MS": "Finance", "C": "Finance",
    "WFC": "Finance", "SCHW": "Finance", "BLK": "Finance", "AXP": "Finance",
    # Payments
    "V": "Payments", "MA": "Payments", "PYPL": "Payments", "SQ": "Payments", "COIN": "Payments", "AFRM": "Payments",
    # Retail
    "WMT": "Retail", "COST": "Retail", "TGT": "Retail", "HD": "Retail", "LOW": "Retail",
    "AMZN": "Retail", "BABA": "Retail", "JD": "Retail", "PDD": "Retail", "MELI": "Retail",
    # Consumer
    "NKE": "Consumer", "LULU": "Consumer", "SBUX": "Consumer", "MCD": "Consumer",
    "CMG": "Consumer", "YUM": "Consumer", "DPZ": "Consumer",
    # Healthcare/Pharma
    "LLY": "Pharma", "PFE": "Pharma", "ABBV": "Pharma", "MRK": "Pharma", "JNJ": "Pharma",
    "UNH": "Pharma", "BMY": "Pharma", "GILD": "Pharma", "AMGN": "Pharma", "REGN": "Pharma",
    "MRNA": "Pharma", "BIIB": "Pharma", "VRTX": "Pharma",
    # Biotech
    "ISRG": "Biotech", "DXCM": "Biotech", "ILMN": "Biotech", "EW": "Biotech",
    # Energy
    "XOM": "Energy", "CVX": "Energy", "SLB": "Energy", "COP": "Energy", "OXY": "Energy",
    "EOG": "Energy", "MPC": "Energy", "PSX": "Energy", "VLO": "Energy", "HAL": "Energy",
    # Media/Entertainment
    "DIS": "Media", "NFLX": "Media", "CMCSA": "Media", "WBD": "Media", "PARA": "Media", "SPOT": "Media",
    # Industrial
    "BA": "Industrial", "CAT": "Industrial", "DE": "Industrial", "UNP": "Industrial",
    "HON": "Industrial", "LMT": "Industrial", "RTX": "Industrial", "GE": "Industrial", "MMM": "Industrial",
    # Cloud/SaaS
    "CRM": "Cloud", "ADBE": "Cloud", "ORCL": "Cloud", "NOW": "Cloud", "SNOW": "Cloud",
    "DDOG": "Cloud", "ZS": "Cloud", "PANW": "Cloud", "CRWD": "Cloud", "NET": "Cloud",
    "MDB": "Cloud", "TEAM": "Cloud", "WDAY": "Cloud", "SPLK": "Cloud", "ESTC": "Cloud",
    # Internet/Social
    "SNAP": "Internet", "PINS": "Internet", "TWTR": "Internet", "MTCH": "Internet", "ABNB": "Internet",
    "UBER": "Internet", "LYFT": "Internet", "DASH": "Internet", "RBLX": "Internet",
    # Telecom
    "T": "Telecom", "VZ": "Telecom", "TMUS": "Telecom",
    # Utilities
    "NEE": "Utilities", "DUK": "Utilities", "SO": "Utilities",
    # REITs
    "AMT": "REIT", "PLD": "REIT", "CCI": "REIT",
    # Materials
    "LIN": "Materials", "APD": "Materials", "FCX": "Materials", "NEM": "Materials",
    # AI/Emerging
    "PLTR": "AI", "AI": "AI", "PATH": "AI", "U": "AI",
}

ALL_TICKERS = list(STOCK_SECTORS.keys())

# ══════════════════════════════════════════════════════════════════
# TIMEZONES
# ══════════════════════════════════════════════════════════════════
ET = pytz.timezone('America/New_York')
CAIRO = pytz.timezone(DISPLAY_TIMEZONE)

# Daily tracking
daily_stats = {
    'date': None,
    'starting_equity': 0,
    'trades_today': 0,
    'pnl_today': 0
}

# ══════════════════════════════════════════════════════════════════
# TELEGRAM ALERTS
# ══════════════════════════════════════════════════════════════════
def send_telegram(message: str, silent: bool = False):
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or "YOUR" in TELEGRAM_BOT_TOKEN:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML",
                "disable_notification": silent}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# MARKET HOURS CHECK
# ══════════════════════════════════════════════════════════════════
def is_market_open() -> tuple:
    """Check if US stock market is open."""
    now_utc = datetime.now(pytz.UTC)
    now_et = now_utc.astimezone(ET)
    now_cairo = now_utc.astimezone(CAIRO)
    
    if now_et.weekday() >= 5:
        return False, f"🔴 Weekend. Cairo: {now_cairo.strftime('%H:%M')}"
    
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if market_open <= now_et <= market_close:
        return True, f"🟢 Market OPEN. Cairo: {now_cairo.strftime('%H:%M')}"
    elif now_et < market_open:
        mins = int((market_open - now_et).total_seconds() / 60)
        return False, f"⏳ Market opens in {mins} min. Cairo: {now_cairo.strftime('%H:%M')}"
    else:
        return False, f"🔴 Market CLOSED. Cairo: {now_cairo.strftime('%H:%M')}"


# ══════════════════════════════════════════════════════════════════
# ALPACA API
# ══════════════════════════════════════════════════════════════════
def get_alpaca_client():
    """Get Alpaca API client."""
    try:
        from alpaca_trade_api import REST
        api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)
        api.get_account()  # Test connection
        return api
    except Exception as e:
        logger.error(f"Alpaca connection failed: {e}")
        return None


def get_account_info(api):
    """Get account balance info."""
    try:
        account = api.get_account()
        return {
            'equity': float(account.equity),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'day_pnl': float(account.equity) - float(account.last_equity)
        }
    except:
        return None


def get_positions(api) -> dict:
    """Get current open positions."""
    try:
        positions = api.list_positions()
        return {p.symbol: {
            'qty': float(p.qty),
            'avg_price': float(p.avg_entry_price),
            'current_price': float(p.current_price),
            'pnl': float(p.unrealized_pl),
            'pnl_pct': float(p.unrealized_plpc) * 100
        } for p in positions}
    except:
        return {}


def execute_bracket_order(api, ticker: str, shares: int, entry: float, sl: float, tp: float) -> bool:
    """Execute a bracket order (Buy + Stop Loss + Take Profit)."""
    try:
        order = api.submit_order(
            symbol=ticker,
            qty=shares,
            side='buy',
            type='market',
            time_in_force='day',
            order_class='bracket',
            stop_loss={'stop_price': round(sl, 2)},
            take_profit={'limit_price': round(tp, 2)}
        )
        
        msg = f"""🟢 <b>ORDER EXECUTED</b>

<b>{ticker}</b> x {shares} shares
<b>Entry:</b> ~${entry:.2f}
<b>Stop Loss:</b> ${sl:.2f} ({(entry-sl)/entry*100:.1f}% risk)
<b>Take Profit:</b> ${tp:.2f} (+{(tp-entry)/entry*100:.1f}%)

<i>Order ID: {order.id[:8]}...</i>"""
        
        logger.info(f"✅ Bought {ticker} x{shares}")
        send_telegram(msg)
        return True
        
    except Exception as e:
        logger.error(f"Trade failed for {ticker}: {e}")
        send_telegram(f"❌ Failed to buy {ticker}: {str(e)[:100]}")
        return False


# ══════════════════════════════════════════════════════════════════
# MARKET REGIME (SPY CHECK)
# ══════════════════════════════════════════════════════════════════
def get_market_regime() -> str:
    """Check market direction via SPY."""
    import yfinance as yf
    
    try:
        spy = yf.Ticker("SPY")
        df = spy.history(period="3mo", interval="1d")
        if df.empty:
            return "NEUTRAL"
        
        c = df["Close"]
        price = float(c.iloc[-1])
        ema20 = c.ewm(span=20).mean().iloc[-1]
        ema50 = c.ewm(span=50).mean().iloc[-1]
        
        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = float((100 - (100 / (1 + gain / loss))).iloc[-1])
        
        chg_20d = (c.iloc[-1] - c.iloc[-20]) / c.iloc[-20] * 100
        
        score = 0
        if price > ema20 > ema50: score += 40
        elif price > ema50: score += 20
        if rsi > 50: score += 20
        if chg_20d > 0: score += 20
        if chg_20d > 3: score += 20
        
        if score >= 60: return "BULLISH"
        elif score >= 30: return "NEUTRAL"
        else: return "BEARISH"
    except:
        return "NEUTRAL"


# ══════════════════════════════════════════════════════════════════
# STOCK SCANNER (10-Factor Win Probability)
# ══════════════════════════════════════════════════════════════════
def analyze_stock(ticker: str) -> dict:
    """Analyze a single stock with 10-factor scoring."""
    import yfinance as yf
    import pandas as pd
    
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="6mo", interval="1d", auto_adjust=True)
        
        if df.empty or len(df) < 50:
            return None
        
        df.columns = [col.lower() for col in df.columns]
        c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
        price = float(c.iloc[-1])
        
        # EMAs
        ema8 = c.ewm(span=8).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        ema200 = c.ewm(span=200).mean() if len(df) >= 200 else c.ewm(span=50).mean()
        
        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        rsi_val = float(rsi.iloc[-1])
        rsi_prev = float(rsi.iloc[-2])
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        hist = macd - signal
        
        # ATR
        tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])
        
        # ADX (simplified)
        plus_dm = h.diff()
        minus_dm = -l.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr_sum = tr.rolling(14).sum()
        plus_di = 100 * plus_dm.rolling(14).sum() / tr_sum
        minus_di = 100 * minus_dm.rolling(14).sum() / tr_sum
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = float(dx.rolling(14).mean().iloc[-1])
        
        # Volume
        vol_avg = v.rolling(20).mean().iloc[-1]
        vol_ratio = v.iloc[-1] / vol_avg if vol_avg > 0 else 0
        
        # ══════════════════════════════════════════════════════════
        # 10-FACTOR SCORING (120 points max)
        # ══════════════════════════════════════════════════════════
        score = 0
        reasons = []
        
        # 1. Trend Alignment (25 pts)
        if price > ema8.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]:
            score += 25
            reasons.append("Perfect EMA stack")
        elif price > ema21.iloc[-1] > ema50.iloc[-1]:
            score += 15
            reasons.append("Bullish trend")
        elif price > ema50.iloc[-1]:
            score += 8
            reasons.append("Above EMA50")
        
        # 2. ADX Strength (15 pts)
        if adx > 30:
            score += 15
            reasons.append(f"Strong trend (ADX {adx:.0f})")
        elif adx > 25:
            score += 10
        elif adx > 20:
            score += 5
        
        # 3. RSI Sweet Spot (15 pts)
        if 40 <= rsi_val <= 55 and rsi_val > rsi_prev:
            score += 15
            reasons.append(f"RSI {rsi_val:.0f} rising")
        elif 35 <= rsi_val <= 60:
            score += 10
        elif rsi_val < 70:
            score += 5
        
        # 4. MACD Confirmation (12 pts)
        if hist.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2]:
            score += 12
            reasons.append("MACD bullish")
        elif hist.iloc[-1] > 0:
            score += 6
        
        # 5. Volume Confirmation (12 pts)
        if vol_ratio > 2.0:
            score += 12
            reasons.append(f"High volume ({vol_ratio:.1f}x)")
        elif vol_ratio > 1.5:
            score += 8
        elif vol_ratio > 1.0:
            score += 4
        
        # 6. Relative Strength vs SPY (10 pts)
        try:
            spy = yf.Ticker("SPY").history(period="1mo")["Close"]
            stock_chg = (c.iloc[-1] - c.iloc[-20]) / c.iloc[-20] * 100
            spy_chg = (spy.iloc[-1] - spy.iloc[-20]) / spy.iloc[-20] * 100
            if stock_chg > spy_chg + 3:
                score += 10
                reasons.append("Beating SPY")
            elif stock_chg > spy_chg:
                score += 5
        except:
            pass
        
        # 7. Price Position (8 pts)
        bb_mid = c.rolling(20).mean().iloc[-1]
        if price > bb_mid:
            score += 8
        
        # 8. Breakout/Pullback (8 pts)
        high_20 = h.rolling(20).max().iloc[-1]
        if price >= high_20 * 0.98:
            score += 8
            reasons.append("Near 20-day high")
        
        # 9. Supertrend (10 pts) - simplified
        st_mult = 3
        st_upper = (h + l) / 2 + st_mult * atr
        if price > st_upper:
            score += 5
        if c.iloc[-1] > c.iloc[-2]:  # Up day
            score += 5
        
        # 10. Momentum (5 pts)
        chg_5d = (c.iloc[-1] - c.iloc[-5]) / c.iloc[-5] * 100
        if 0 < chg_5d < 8:
            score += 5
            reasons.append(f"+{chg_5d:.1f}% this week")
        
        # Calculate win probability
        win_prob = min(95, int(score / 120 * 100))
        
        # ══════════════════════════════════════════════════════════
        # TRADE LEVELS
        # ══════════════════════════════════════════════════════════
        sl = price - atr * 1.5
        tp = price + atr * 3.5
        sl_pct = (price - sl) / price * 100
        tp_pct = (tp - price) / price * 100
        rr = tp_pct / sl_pct if sl_pct > 0 else 0
        
        # Position sizing
        max_loss = CAPITAL * (RISK_PER_TRADE_PCT / 100)
        max_pos = CAPITAL * (MAX_POSITION_PCT / 100)
        loss_per_share = price - sl
        shares = min(max_loss / loss_per_share, max_pos / price) if loss_per_share > 0 else 0
        shares = int(shares)
        
        return {
            'ticker': ticker,
            'sector': STOCK_SECTORS.get(ticker, 'Unknown'),
            'price': price,
            'win_prob': win_prob,
            'shares': shares,
            'sl': sl,
            'tp': tp,
            'sl_pct': sl_pct,
            'tp_pct': tp_pct,
            'rr': rr,
            'rsi': rsi_val,
            'adx': adx,
            'vol_ratio': vol_ratio,
            'reasons': reasons
        }
        
    except Exception as e:
        logger.debug(f"Error analyzing {ticker}: {e}")
        return None


def run_scanner() -> list:
    """Scan all stocks and return top 3 picks."""
    logger.info(f"Scanning {len(ALL_TICKERS)} stocks...")
    
    results = []
    
    # Parallel scanning
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in ALL_TICKERS}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    
    # Filter criteria
    filtered = [r for r in results if (
        r['win_prob'] >= MIN_WIN_PROB and
        r['tp_pct'] >= MIN_TARGET_PCT and
        r['rr'] >= MIN_REWARD_RISK and
        r['rsi'] < 75 and  # Not overbought
        r['shares'] >= 1
    )]
    
    # Sector diversification - max 1 per sector in top 3
    filtered.sort(key=lambda x: x['win_prob'], reverse=True)
    
    final_picks = []
    used_sectors = set()
    
    for pick in filtered:
        if pick['sector'] not in used_sectors:
            final_picks.append(pick)
            used_sectors.add(pick['sector'])
        if len(final_picks) >= 3:
            break
    
    logger.info(f"Found {len(final_picks)} qualifying stocks")
    return final_picks


# ══════════════════════════════════════════════════════════════════
# MAIN BOT LOGIC
# ══════════════════════════════════════════════════════════════════
def run_bot():
    """Main bot execution."""
    global daily_stats
    
    now_cairo = datetime.now(pytz.UTC).astimezone(CAIRO)
    logger.info("=" * 60)
    logger.info(f"🤖 Bot started at {now_cairo.strftime('%Y-%m-%d %H:%M')} Cairo")
    
    # Check market hours
    is_open, market_msg = is_market_open()
    logger.info(market_msg)
    
    if not is_open:
        send_telegram(f"⏰ {market_msg}\nBot will check again later.", silent=True)
        return
    
    # Check market regime
    regime = get_market_regime()
    logger.info(f"Market Regime: {regime}")
    
    if regime == "BEARISH":
        msg = "🔴 <b>MARKET BEARISH</b>\nSkipping trades to protect capital."
        logger.info("Skipping - bearish market")
        send_telegram(msg)
        return
    
    # Connect to Alpaca
    api = get_alpaca_client()
    if not api:
        send_telegram("❌ Failed to connect to Alpaca")
        return
    
    account = get_account_info(api)
    positions = get_positions(api)
    
    # Reset daily stats
    today = date.today()
    if daily_stats['date'] != today:
        daily_stats = {
            'date': today,
            'starting_equity': account['equity'],
            'trades_today': 0,
            'pnl_today': 0
        }
    
    # Check daily loss limit
    daily_pnl = account['equity'] - daily_stats['starting_equity']
    daily_pnl_pct = daily_pnl / daily_stats['starting_equity'] * 100
    
    if daily_pnl_pct <= -DAILY_LOSS_LIMIT_PCT:
        msg = f"🛑 <b>DAILY LOSS LIMIT HIT</b>\nDown ${abs(daily_pnl):,.0f} ({daily_pnl_pct:.1f}%)\nNo more trades today."
        logger.warning("Daily loss limit reached")
        send_telegram(msg)
        return
    
    # Check position limit
    if len(positions) >= MAX_OPEN_POSITIONS:
        msg = f"⚠️ Max {MAX_OPEN_POSITIONS} positions reached.\nWaiting for exits..."
        logger.info("Position limit reached")
        send_telegram(msg, silent=True)
        return
    
    # Log current positions
    if positions:
        pos_summary = "\n".join([f"• {k}: {v['pnl_pct']:+.1f}%" for k, v in positions.items()])
        logger.info(f"Open positions:\n{pos_summary}")
    
    # Run scanner
    picks = run_scanner()
    
    if not picks:
        msg = "📊 No high-probability setups found. Waiting..."
        logger.info(msg)
        send_telegram(msg, silent=True)
        return
    
    # Send picks summary
    picks_text = "\n".join([
        f"{i+1}. <b>{p['ticker']}</b> ({p['sector']}) — {p['win_prob']}% prob, +{p['tp_pct']:.1f}% target"
        for i, p in enumerate(picks)
    ])
    
    summary = f"""📊 <b>SCAN COMPLETE</b>

<b>Market:</b> {regime}
<b>Balance:</b> ${account['equity']:,.0f}
<b>Open:</b> {len(positions)}/{MAX_OPEN_POSITIONS} positions

<b>Top Picks:</b>
{picks_text}

Executing trades..."""
    
    send_telegram(summary)
    
    # Execute trades
    trades_executed = 0
    slots_available = MAX_OPEN_POSITIONS - len(positions)
    
    for pick in picks[:slots_available]:
        # Skip if already own
        if pick['ticker'] in positions:
            logger.info(f"Skipping {pick['ticker']} - already own")
            continue
        
        success = execute_bracket_order(
            api=api,
            ticker=pick['ticker'],
            shares=pick['shares'],
            entry=pick['price'],
            sl=pick['sl'],
            tp=pick['tp']
        )
        
        if success:
            trades_executed += 1
            daily_stats['trades_today'] += 1
        
        time.sleep(1)
    
    # Final summary
    account = get_account_info(api)
    final = f"""✅ <b>BOT RUN COMPLETE</b>

<b>Trades:</b> {trades_executed}
<b>Balance:</b> ${account['equity']:,.0f}
<b>Today's P&L:</b> ${daily_pnl:+,.0f} ({daily_pnl_pct:+.1f}%)
<b>Time:</b> {now_cairo.strftime('%H:%M')} Cairo"""
    
    send_telegram(final)


def main():
    """Entry point."""
    loop_mode = '--loop' in sys.argv
    
    if loop_mode:
        logger.info("Starting LOOP mode")
        send_telegram("🤖 Bot started in LOOP mode\nChecks every 30 minutes during market hours")
        
        while True:
            try:
                run_bot()
            except Exception as e:
                logger.error(f"Bot error: {e}")
                send_telegram(f"❌ Error: {str(e)[:100]}")
            
            logger.info("Sleeping 30 minutes...")
            time.sleep(30 * 60)
    else:
        try:
            run_bot()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            send_telegram(f"❌ Error: {str(e)[:100]}")


if __name__ == "__main__":
    main()
