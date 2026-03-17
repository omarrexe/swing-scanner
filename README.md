# Swing Trading Scanner

A beginner-friendly US stock market scanner built with Python and Streamlit.
It analyzes stocks using 7 scientific checks and generates a complete trade plan
based on your available capital.

---

## What It Does

- Scans 60+ US stocks across major sectors
- Runs 7 independent technical checks on each stock
- Explains every signal in plain English
- Calculates exact Stop Loss, Take Profit, and position size based on your capital
- Includes an interactive price chart with trade levels
- Allows searching and analyzing any US stock ticker directly

---

## How It Works

The scanner uses the following indicators:

1. EMA Stack — checks if the trend is aligned upward
2. RSI Momentum — checks if buying pressure is in a healthy zone
3. MACD — checks if momentum is positive and accelerating
4. Volume — checks if institutions are actively buying
5. Bollinger Bands — checks if the price has room to move up
6. VWAP — checks if buyers are in control intraday
7. News Sentiment — checks if recent headlines support the move

A stock needs at least 4 out of 7 checks to pass before a BUY signal is issued.

---

## Risk Management

The scanner follows professional risk rules automatically:

- Never risk more than 1.5% of your total capital on a single trade
- Never allocate more than 30% of your capital to one stock
- Stop Loss is set at 1.5x the Average True Range below entry
- Take Profit is set at 3.5x the Average True Range above entry
- Minimum Risk to Reward ratio required: 1:2

---

## Installation

```
pip install streamlit yfinance pandas numpy plotly requests
streamlit run app.py
```

---

## Deploy on Streamlit Cloud (Free)

1. Fork or upload this repository to your GitHub account
2. Go to share.streamlit.io
3. Click New app
4. Select this repository and set the main file to app.py
5. Click Deploy

The app will be live at a public URL within a few minutes.

---

## Project Structure

```
swing-scanner/
    app.py              Main application
    requirements.txt    Python dependencies
    README.md           This file
```

---

## Disclaimer

This tool is for educational and informational purposes only.
It is not financial advice. Always do your own research before
making any investment decisions. Past signals do not guarantee
future results.
