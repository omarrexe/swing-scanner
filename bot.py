#!/usr/bin/env python3
"""
🤖 Swing Trading Auto-Bot
Runs independently, executes trades on Alpaca, sends Telegram alerts.

Usage:
    python bot.py              # Run once
    python bot.py --loop       # Run continuously (checks every 30 min)

For PythonAnywhere: Set up a Scheduled Task to run every hour.
"""

import os
import sys
import time
import logging
from datetime import datetime
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
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
        CAPITAL, RISK_PER_TRADE_PCT, MAX_POSITION_PCT,
        MIN_WIN_PROB, MAX_TRADES_PER_RUN, DISPLAY_TIMEZONE
    )
except ImportError:
    logger.error("config.py not found! Copy config.py.example to config.py and fill in your keys.")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════
# TIMEZONES
# ══════════════════════════════════════════════════════════════════
ET = pytz.timezone('America/New_York')  # US Eastern Time
CAIRO = pytz.timezone(DISPLAY_TIMEZONE)  # Your local timezone

# ══════════════════════════════════════════════════════════════════
# TELEGRAM ALERTS
# ══════════════════════════════════════════════════════════════════
def send_telegram(message: str):
    """Send a message to your Telegram."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.warning("Telegram not configured. Skipping alert.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram sent: {message[:50]}...")
            return True
        else:
            logger.error(f"Telegram failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# MARKET HOURS CHECK
# ══════════════════════════════════════════════════════════════════
def is_market_open() -> tuple:
    """
    Check if US stock market is open.
    Returns: (is_open: bool, message: str)
    
    US Market Hours: Monday-Friday, 9:30 AM - 4:00 PM Eastern Time
    In Cairo time: ~4:30 PM - 11:00 PM (varies with DST)
    """
    now_utc = datetime.now(pytz.UTC)
    now_et = now_utc.astimezone(ET)
    now_cairo = now_utc.astimezone(CAIRO)
    
    # Check if weekend
    if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False, f"Market CLOSED (Weekend). Cairo time: {now_cairo.strftime('%H:%M')}"
    
    # Check if within market hours (9:30 AM - 4:00 PM ET)
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if market_open <= now_et <= market_close:
        return True, f"Market OPEN. Cairo: {now_cairo.strftime('%H:%M')} | NY: {now_et.strftime('%H:%M')}"
    else:
        # Calculate time until open
        if now_et < market_open:
            mins_until = int((market_open - now_et).total_seconds() / 60)
            return False, f"Market opens in {mins_until} min. Cairo: {now_cairo.strftime('%H:%M')}"
        else:
            return False, f"Market CLOSED for today. Cairo: {now_cairo.strftime('%H:%M')}"


def get_market_hours_cairo() -> str:
    """Get today's market hours in Cairo time."""
    now_utc = datetime.now(pytz.UTC)
    now_et = now_utc.astimezone(ET)
    
    # Market open/close in ET
    market_open_et = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close_et = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # Convert to Cairo
    market_open_cairo = market_open_et.astimezone(CAIRO)
    market_close_cairo = market_close_et.astimezone(CAIRO)
    
    return f"{market_open_cairo.strftime('%H:%M')} - {market_close_cairo.strftime('%H:%M')} Cairo"


# ══════════════════════════════════════════════════════════════════
# ALPACA API INTEGRATION
# ══════════════════════════════════════════════════════════════════
def get_alpaca_client():
    """Get Alpaca API client."""
    try:
        from alpaca_trade_api import REST
        api = REST(
            key_id=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            base_url=ALPACA_BASE_URL
        )
        # Test connection
        account = api.get_account()
        logger.info(f"Alpaca connected. Balance: ${float(account.equity):,.2f}")
        return api
    except Exception as e:
        logger.error(f"Alpaca connection failed: {e}")
        return None


def get_current_positions(api) -> dict:
    """Get current open positions."""
    try:
        positions = api.list_positions()
        return {p.symbol: {
            'qty': float(p.qty),
            'avg_price': float(p.avg_entry_price),
            'current_price': float(p.current_price),
            'unrealized_pl': float(p.unrealized_pl),
            'unrealized_plpc': float(p.unrealized_plpc) * 100
        } for p in positions}
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        return {}


def execute_trade(api, ticker: str, shares: float, sl: float, tp: float) -> bool:
    """
    Execute a bracket order on Alpaca.
    
    Bracket order = Market Buy + Stop Loss + Take Profit
    """
    try:
        # Check if we already have a position
        positions = get_current_positions(api)
        if ticker in positions:
            msg = f"⏭️ Skipping {ticker} — Already have {positions[ticker]['qty']:.0f} shares"
            logger.info(msg)
            send_telegram(msg)
            return False
        
        # Round shares to whole number
        shares = int(shares)
        if shares < 1:
            logger.warning(f"Cannot buy {ticker}: shares={shares} < 1")
            return False
        
        # Submit bracket order
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
        
        msg = f"""🟢 <b>BUY ORDER EXECUTED</b>

<b>Ticker:</b> {ticker}
<b>Shares:</b> {shares}
<b>Stop Loss:</b> ${sl:.2f}
<b>Take Profit:</b> ${tp:.2f}
<b>Order ID:</b> {order.id}"""
        
        logger.info(f"Order placed: {ticker} x{shares} | SL: ${sl:.2f} | TP: ${tp:.2f}")
        send_telegram(msg)
        return True
        
    except Exception as e:
        msg = f"❌ Trade failed for {ticker}: {str(e)}"
        logger.error(msg)
        send_telegram(msg)
        return False


# ══════════════════════════════════════════════════════════════════
# SCANNER LOGIC (Simplified from app.py)
# ══════════════════════════════════════════════════════════════════
def run_scanner():
    """
    Run the swing trading scanner and return top picks.
    This is a simplified version of the app.py scanner.
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np
    
    try:
        import pandas_ta as ta
    except ImportError:
        logger.warning("pandas_ta not available, using basic indicators")
        ta = None
    
    # Stock universe (same as app.py)
    TICKERS = [
        "AAPL", "MSFT", "GOOGL", "META", "AMZN", "NVDA", "AMD", "TSLA",
        "JPM", "BAC", "GS", "V", "MA", "PYPL", "SQ",
        "WMT", "COST", "TGT", "HD", "NKE",
        "LLY", "PFE", "ABBV", "MRK", "JNJ",
        "XOM", "CVX", "SLB", "COP",
        "DIS", "NFLX", "CMCSA",
        "BA", "CAT", "DE", "UNP",
        "CRM", "ADBE", "ORCL", "NOW"
    ]
    
    results = []
    
    for ticker in TICKERS:
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="6mo", interval="1d", auto_adjust=True)
            
            if df.empty or len(df) < 50:
                continue
            
            df.columns = [c.lower() for c in df.columns]
            c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
            price = float(c.iloc[-1])
            
            # Calculate indicators
            ema8 = c.ewm(span=8, adjust=False).mean()
            ema21 = c.ewm(span=21, adjust=False).mean()
            ema50 = c.ewm(span=50, adjust=False).mean()
            
            # RSI
            delta = c.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + gain / loss))
            
            # MACD
            ema12 = c.ewm(span=12, adjust=False).mean()
            ema26 = c.ewm(span=26, adjust=False).mean()
            macd_hist = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
            
            # ATR
            tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            # Volume
            vol_ratio = v.iloc[-1] / v.rolling(20).mean().iloc[-1]
            
            # Win probability scoring (simplified)
            score = 0
            
            # Trend alignment
            if price > ema8.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1]:
                score += 30
            elif price > ema21.iloc[-1] > ema50.iloc[-1]:
                score += 20
            elif price > ema50.iloc[-1]:
                score += 10
            
            # RSI
            rsi_val = float(rsi.iloc[-1])
            if 40 <= rsi_val <= 60:
                score += 20
            elif 30 <= rsi_val <= 70:
                score += 10
            
            # MACD
            if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-1] > macd_hist.iloc[-2]:
                score += 20
            elif macd_hist.iloc[-1] > 0:
                score += 10
            
            # Volume
            if vol_ratio > 1.5:
                score += 15
            elif vol_ratio > 1.0:
                score += 8
            
            # Momentum
            chg_5d = (c.iloc[-1] - c.iloc[-5]) / c.iloc[-5] * 100
            if 0 < chg_5d < 10:
                score += 15
            
            win_prob = min(95, score)
            
            # Calculate trade levels
            atr_val = float(atr.iloc[-1])
            sl = price - atr_val * 1.5
            tp = price + atr_val * 3.5
            sl_pct = (price - sl) / price * 100
            tp_pct = (tp - price) / price * 100
            rr = tp_pct / sl_pct if sl_pct > 0 else 0
            
            # Position sizing
            max_loss = CAPITAL * (RISK_PER_TRADE_PCT / 100)
            max_pos = CAPITAL * (MAX_POSITION_PCT / 100)
            loss_per_share = price - sl
            shares = min(max_loss / loss_per_share, max_pos / price) if loss_per_share > 0 else 0
            
            # Filter criteria
            if win_prob < MIN_WIN_PROB:
                continue
            if tp_pct < 5.0:
                continue
            if rr < 2.0:
                continue
            if rsi_val > 75:  # Overbought
                continue
            
            results.append({
                'ticker': ticker,
                'price': price,
                'win_prob': win_prob,
                'shares': shares,
                'sl': sl,
                'tp': tp,
                'sl_pct': sl_pct,
                'tp_pct': tp_pct,
                'rr': rr,
                'rsi': rsi_val,
            })
            
        except Exception as e:
            logger.debug(f"Error scanning {ticker}: {e}")
            continue
    
    # Sort by win probability
    results.sort(key=lambda x: x['win_prob'], reverse=True)
    return results[:MAX_TRADES_PER_RUN]


def get_market_regime() -> str:
    """Check if SPY indicates bullish, neutral, or bearish market."""
    import yfinance as yf
    
    try:
        spy = yf.Ticker("SPY")
        df = spy.history(period="3mo", interval="1d")
        
        if df.empty:
            return "NEUTRAL"
        
        c = df["Close"]
        price = float(c.iloc[-1])
        
        ema20 = c.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = c.ewm(span=50, adjust=False).mean().iloc[-1]
        
        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        rsi_val = float(rsi.iloc[-1])
        
        # 20-day change
        chg_20d = (c.iloc[-1] - c.iloc[-20]) / c.iloc[-20] * 100
        
        score = 0
        
        # EMA alignment
        if price > ema20 > ema50:
            score += 40
        elif price > ema50:
            score += 20
        
        # RSI
        if rsi_val > 50:
            score += 20
        
        # Momentum
        if chg_20d > 0:
            score += 20
        if chg_20d > 3:
            score += 20
        
        if score >= 60:
            return "BULLISH"
        elif score >= 30:
            return "NEUTRAL"
        else:
            return "BEARISH"
            
    except Exception as e:
        logger.error(f"Market regime check failed: {e}")
        return "NEUTRAL"


# ══════════════════════════════════════════════════════════════════
# MAIN BOT LOGIC
# ══════════════════════════════════════════════════════════════════
def run_bot():
    """Main bot execution."""
    now_cairo = datetime.now(pytz.UTC).astimezone(CAIRO)
    logger.info(f"{'='*50}")
    logger.info(f"🤖 Bot started at {now_cairo.strftime('%Y-%m-%d %H:%M')} Cairo time")
    logger.info(f"US Market hours today: {get_market_hours_cairo()}")
    
    # Check market hours
    is_open, market_msg = is_market_open()
    logger.info(market_msg)
    
    if not is_open:
        send_telegram(f"⏰ {market_msg}\nBot will check again later.")
        return
    
    # Check market regime
    regime = get_market_regime()
    logger.info(f"Market Regime: {regime}")
    
    if regime == "BEARISH":
        msg = "🔴 Market is BEARISH. Skipping trades to protect capital."
        logger.info(msg)
        send_telegram(msg)
        return
    
    # Connect to Alpaca
    api = get_alpaca_client()
    if api is None:
        send_telegram("❌ Failed to connect to Alpaca. Check your API keys.")
        return
    
    # Get current positions
    positions = get_current_positions(api)
    if positions:
        pos_msg = "\n".join([f"  • {k}: {v['qty']:.0f} shares ({v['unrealized_plpc']:+.1f}%)" 
                            for k, v in positions.items()])
        logger.info(f"Current positions:\n{pos_msg}")
    
    # Run scanner
    logger.info("Running scanner...")
    picks = run_scanner()
    
    if not picks:
        msg = "📊 No high-probability setups found right now. Waiting for better opportunities."
        logger.info(msg)
        send_telegram(msg)
        return
    
    # Send summary
    picks_msg = "\n".join([f"  {i+1}. {p['ticker']} — {p['win_prob']:.0f}% prob, +{p['tp_pct']:.1f}% target" 
                          for i, p in enumerate(picks)])
    
    summary = f"""📊 <b>SCAN COMPLETE</b>

<b>Market:</b> {regime}
<b>Top {len(picks)} Picks:</b>
{picks_msg}

Executing trades..."""
    
    send_telegram(summary)
    
    # Execute trades
    trades_executed = 0
    for pick in picks:
        success = execute_trade(
            api=api,
            ticker=pick['ticker'],
            shares=pick['shares'],
            sl=pick['sl'],
            tp=pick['tp']
        )
        if success:
            trades_executed += 1
        time.sleep(1)  # Small delay between orders
    
    # Final summary
    account = api.get_account()
    final_msg = f"""✅ <b>BOT RUN COMPLETE</b>

<b>Trades Executed:</b> {trades_executed}/{len(picks)}
<b>Account Balance:</b> ${float(account.equity):,.2f}
<b>Buying Power:</b> ${float(account.buying_power):,.2f}
<b>Cairo Time:</b> {now_cairo.strftime('%H:%M')}"""
    
    logger.info(f"Bot run complete. {trades_executed} trades executed.")
    send_telegram(final_msg)


def main():
    """Entry point."""
    # Check for loop mode
    loop_mode = '--loop' in sys.argv
    
    if loop_mode:
        logger.info("Starting in LOOP mode (runs every 30 minutes)")
        send_telegram("🤖 Bot started in LOOP mode. Will check every 30 minutes.")
        
        while True:
            try:
                run_bot()
            except Exception as e:
                logger.error(f"Bot error: {e}")
                send_telegram(f"❌ Bot error: {str(e)}")
            
            # Sleep 30 minutes
            logger.info("Sleeping for 30 minutes...")
            time.sleep(30 * 60)
    else:
        # Single run
        try:
            run_bot()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            send_telegram(f"❌ Bot error: {str(e)}")


if __name__ == "__main__":
    main()
