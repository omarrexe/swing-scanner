"""
Configuration file for the Trading Bot
Fill in your API keys below.
"""

# ══════════════════════════════════════════════════════════════════
# ALPACA API (Paper Trading - FREE)
# Get your keys at: https://app.alpaca.markets/paper/dashboard/overview
# ══════════════════════════════════════════════════════════════════
ALPACA_API_KEY = "YOUR_ALPACA_API_KEY"
ALPACA_SECRET_KEY = "YOUR_ALPACA_SECRET_KEY"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper trading (fake money)

# ══════════════════════════════════════════════════════════════════
# TELEGRAM BOT (FREE)
# 1. Message @BotFather on Telegram, send /newbot, follow steps
# 2. You'll get a token like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
# 3. Message @userinfobot to get your Chat ID
# ══════════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# ══════════════════════════════════════════════════════════════════
# BOT SETTINGS
# ══════════════════════════════════════════════════════════════════
CAPITAL = 10000  # Your paper trading capital
RISK_PER_TRADE_PCT = 1.5  # Max 1.5% risk per trade
MAX_POSITION_PCT = 30.0  # Max 30% of capital in one stock
MIN_WIN_PROB = 65  # Only trade stocks with 65%+ win probability
MAX_TRADES_PER_RUN = 3  # Max trades per bot run

# Timezone for display (bot always checks US market hours internally)
DISPLAY_TIMEZONE = "Africa/Cairo"
