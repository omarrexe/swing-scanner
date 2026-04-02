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
    page_title="TradingPro • Elite Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
#  PREMIUM SAAS UI — ULTRA PROFESSIONAL TRADING PLATFORM
# ══════════════════════════════════════════════════════════════════
CSS = """
<style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
    
    /* CSS Variables for Premium Theme */
    :root {
        --bg-primary: #0B0E14;
        --bg-secondary: #151822;
        --bg-tertiary: #1F2937;
        --bg-card: rgba(31, 41, 55, 0.6);
        --bg-glass: rgba(255, 255, 255, 0.02);
        
        --text-primary: #F8FAFC;
        --text-secondary: #CBD5E1;
        --text-muted: #64748B;
        
        --accent-primary: #00FF87;
        --accent-danger: #FF3B30;
        --accent-warning: #FFD60A;
        --accent-purple: #8B5CF6;
        --accent-cyan: #06B6D4;
        
        --border-glass: rgba(255, 255, 255, 0.08);
        --shadow-glow: 0 0 30px rgba(139, 92, 246, 0.15);
        --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.3);
        
        --font-mono: 'JetBrains Mono', 'Consolas', monospace;
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global Reset & Base Styles */
    * { 
        font-family: var(--font-sans);
        box-sizing: border-box;
    }
    
    /* Premium Background */
    .stApp {
        background: var(--bg-primary);
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(6, 182, 212, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(0, 255, 135, 0.04) 0%, transparent 50%);
        min-height: 100vh;
        position: relative;
    }
    
    /* Animated Background Particles */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: 
            radial-gradient(circle at 25% 25%, rgba(139, 92, 246, 0.1) 0%, transparent 25%),
            radial-gradient(circle at 75% 75%, rgba(6, 182, 212, 0.08) 0%, transparent 25%);
        animation: float 20s ease-in-out infinite;
        pointer-events: none;
        z-index: -1;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(30px, -30px) rotate(1deg); }
        66% { transform: translate(-20px, 20px) rotate(-1deg); }
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Container Layout */
    .main .block-container { 
        max-width: 1200px;
        padding: 2rem;
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu, footer, header, .stDeployButton { visibility: hidden; }
    
    /* Premium Header */
    .trading-header {
        text-align: center;
        padding: 3rem 0;
        animation: slideUp 0.8s ease-out;
    }
    
    .brand-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-purple) 50%, var(--accent-cyan) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        margin: 0;
    }
    
    .brand-subtitle {
        font-size: 1.1rem;
        color: var(--text-muted);
        font-weight: 500;
        margin-top: 0.5rem;
        letter-spacing: 0.5px;
    }
    
    /* Premium Market Status */
    .market-status {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        padding: 12px 24px;
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 2rem auto;
        transition: all 0.3s ease;
    }
    
    .market-status:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
    }
    
    .status-bullish { 
        color: var(--accent-primary);
        border-color: rgba(0, 255, 135, 0.2);
    }
    .status-neutral { 
        color: var(--accent-warning);
        border-color: rgba(255, 214, 10, 0.2);
    }
    .status-bearish { 
        color: var(--accent-danger);
        border-color: rgba(255, 59, 48, 0.2);
    }
    
    /* Premium Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-cyan) 100%);
        color: var(--text-primary);
        border: none;
        border-radius: 16px;
        font-family: var(--font-sans);
        font-weight: 700;
        font-size: 1.1rem;
        padding: 1.2rem 2.5rem;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; right: 0; bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.6s;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 40px rgba(139, 92, 246, 0.4);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Premium Signal Cards */
    .signal-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: 24px;
        padding: 2rem;
        margin: 1.5rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: slideUp 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .signal-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-purple), var(--accent-cyan));
    }
    
    .signal-card:hover {
        transform: translateY(-8px);
        box-shadow: var(--shadow-card);
        border-color: rgba(139, 92, 246, 0.3);
    }
    
    .signal-primary {
        border: 2px solid var(--accent-primary);
        box-shadow: 0 0 30px rgba(0, 255, 135, 0.2);
    }
    
    /* Financial Typography */
    .ticker-display {
        display: flex;
        align-items: baseline;
        gap: 16px;
        margin-bottom: 1rem;
    }
    
    .ticker-symbol {
        font-family: var(--font-mono);
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-primary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }
    
    .ticker-price {
        font-family: var(--font-mono);
        font-size: 1.8rem;
        color: var(--text-secondary);
        font-weight: 600;
    }
    
    .sector-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.3);
        color: var(--accent-purple);
        padding: 8px 16px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .action-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .badge-primary {
        background: var(--accent-primary);
        color: var(--bg-primary);
    }
    
    .badge-secondary {
        background: var(--bg-tertiary);
        color: var(--text-muted);
        border: 1px solid var(--border-glass);
    }
    
    /* Premium Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(139, 92, 246, 0.3);
        box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1);
    }
    
    .metric-value {
        font-family: var(--font-mono);
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: var(--text-muted);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-icon {
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        opacity: 0.7;
    }
    
    /* Financial Colors */
    .text-bullish { color: var(--accent-primary) !important; }
    .text-bearish { color: var(--accent-danger) !important; }
    .text-neutral { color: var(--accent-warning) !important; }
    .text-purple { color: var(--accent-purple) !important; }
    .text-cyan { color: var(--accent-cyan) !important; }
    
    /* Premium Capital Input */
    .capital-section {
        background: rgba(6, 182, 212, 0.08);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(20px);
    }
    
    .capital-title {
        display: flex;
        align-items: center;
        gap: 12px;
        color: var(--accent-cyan);
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    
    /* Premium Statistics */
    .stats-container {
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        backdrop-filter: blur(20px);
    }
    
    .stats-title {
        display: flex;
        align-items: center;
        gap: 12px;
        color: var(--accent-purple);
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        text-align: center;
    }
    
    /* Professional Reason Items */
    .reason-item {
        background: var(--bg-glass);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        transition: all 0.3s ease;
    }
    
    .reason-item:hover {
        transform: translateX(4px);
        border-color: rgba(139, 92, 246, 0.3);
    }
    
    .reason-title {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--text-primary);
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }
    
    .reason-text {
        color: var(--text-secondary);
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    /* Professional Empty State */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        animation: fadeIn 0.8s ease-out;
    }
    
    .empty-icon {
        font-size: 4rem;
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-cyan) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }
    
    .empty-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.8rem;
    }
    
    .empty-text {
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.6;
        max-width: 500px;
        margin: 0 auto;
    }
    
    /* Premium Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-glass), transparent);
        margin: 3rem 0;
    }
    
    /* Input Styling */
    .stNumberInput input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-family: var(--font-mono) !important;
        font-weight: 600 !important;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(20px) !important;
    }
    
    /* Signal Count Header */
    .signals-header {
        text-align: center;
        margin: 2rem 0;
        animation: slideUp 0.6s ease-out 0.2s both;
    }
    
    .signals-count {
        color: var(--accent-primary);
        font-size: 1.4rem;
        font-weight: 700;
        font-family: var(--font-mono);
    }
    
    .signals-subtitle {
        color: var(--text-muted);
        margin-left: 12px;
        font-size: 0.9rem;
    }
    
    /* Risk/Reward Footer */
    .trade-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border-glass);
        color: var(--text-muted);
        font-size: 0.9rem;
        font-family: var(--font-mono);
    }
</style>
"""
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
        reasons.append(("<i class='fas fa-chart-line text-bullish'></i> Perfect Trend", "All EMAs aligned bullish"))
    elif ind["price"] > ind["ema8"] > ind["ema21"] > ind["ema50"]:
        score += 25
        reasons.append(("<i class='fas fa-trending-up text-bullish'></i> Strong Trend", "Short & mid EMAs aligned"))
    elif ind["price"] > ind["ema21"] > ind["ema50"]:
        score += 15
        reasons.append(("<i class='fas fa-arrow-up text-bullish'></i> Uptrend", "Above key moving averages"))
    
    if ind["adx"] > 30 and ind["plus_di"] > ind["minus_di"]:
        score += 20
        reasons.append(("<i class='fas fa-tachometer-alt text-purple'></i> Strong ADX", f"ADX {ind['adx']:.0f} with bullish direction"))
    elif ind["adx"] > 25:
        score += 12
    elif ind["adx"] > 20:
        score += 5
    
    if 45 <= ind["rsi"] <= 60 and ind["rsi"] > ind["rsi_prev"]:
        score += 20
        reasons.append(("<i class='fas fa-signal text-cyan'></i> RSI Rising", f"RSI {ind['rsi']:.0f}, momentum building"))
    elif 40 <= ind["rsi"] <= 65:
        score += 12
    elif ind["rsi"] < 70:
        score += 5
    
    if ind["macd_hist"] > 0 and ind["macd_hist"] > ind["macd_prev"]:
        score += 15
        reasons.append(("<i class='fas fa-wave-square text-purple'></i> MACD Bullish", "Histogram positive and rising"))
    elif ind["macd_hist"] > 0:
        score += 8
    
    if ind["vol_ratio"] > 1.5:
        score += 15
        reasons.append(("<i class='fas fa-volume-up text-cyan'></i> High Volume", f"{ind['vol_ratio']:.1f}x average volume"))
    elif ind["vol_ratio"] > 1.2:
        score += 10
    elif ind["vol_ratio"] > 1.0:
        score += 5
    
    if ind["supertrend_bull"]:
        score += 15
        reasons.append(("<i class='fas fa-rocket text-bullish'></i> Supertrend", "Confirms upward momentum"))
    
    if 2 < ind["chg_5d"] < 10:
        score += 15
        reasons.append(("<i class='fas fa-fire text-warning'></i> Momentum", f"+{ind['chg_5d']:.1f}% this week"))
    elif 0 < ind["chg_5d"] < 15:
        score += 8
    
    if ind["rsi"] < 65:
        score += 15
        reasons.append(("<i class='fas fa-arrow-circle-up text-bullish'></i> Room to Run", "Not overbought yet"))
    
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
    
    # Premium neon candlesticks
    fig.add_trace(go.Candlestick(
        x=df2.index, open=df2["open"], high=df2["high"],
        low=df2["low"], close=df2["close"],
        name="Price",
        increasing_line_color="#00FF87",  # Neon green
        decreasing_line_color="#FF3B30",  # Neon red
        increasing_fillcolor="rgba(0, 255, 135, 0.8)",
        decreasing_fillcolor="rgba(255, 59, 48, 0.8)",
    ))
    
    # Neon EMA lines
    fig.add_trace(go.Scatter(
        x=df2.index, y=ema8, 
        name="EMA 8", 
        line=dict(color="#8B5CF6", width=2, dash="dot")  # Purple
    ))
    fig.add_trace(go.Scatter(
        x=df2.index, y=ema21, 
        name="EMA 21", 
        line=dict(color="#06B6D4", width=2, dash="dash")  # Cyan
    ))
    
    # Professional stop/target lines
    fig.add_hline(
        y=pos["sl"], 
        line_dash="dash", 
        line_color="#FF3B30", 
        line_width=2,
        annotation_text="Stop Loss",
        annotation_font_color="#FF3B30"
    )
    fig.add_hline(
        y=pos["tp"], 
        line_dash="dash", 
        line_color="#00FF87", 
        line_width=2,
        annotation_text="Target",
        annotation_font_color="#00FF87"
    )
    
    # Premium dark theme layout
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent to match cards
        plot_bgcolor="rgba(11, 14, 20, 0.95)",  # Match --bg-primary with slight opacity
        font=dict(
            family="'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            color="#CBD5E1",  # --text-secondary
            size=11
        ),
        # Remove all gridlines for clean look
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.05)",
            showgrid=False,  # Minimal gridlines
            zeroline=False,
            linecolor="rgba(255, 255, 255, 0.08)"
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.05)",
            showgrid=False,  # Minimal gridlines
            zeroline=False,
            side="right",
            linecolor="rgba(255, 255, 255, 0.08)"
        ),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h", 
            y=1.02,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(color="#CBD5E1")
        ),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        # Add subtle border to match card styling
        shapes=[
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0, x1=1, y1=1,
                line=dict(
                    color="rgba(255, 255, 255, 0.08)",
                    width=1
                ),
                fillcolor="rgba(0,0,0,0)"
            )
        ]
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

# Premium Header
st.markdown("""
<div class="trading-header">
    <h1 class="brand-title">TradingPro Elite</h1>
    <p class="brand-subtitle">Professional-Grade Swing Trading Scanner</p>
</div>
""", unsafe_allow_html=True)

# Market Status with Professional Icons
regime, regime_score, regime_msg = get_market_regime()
status_icon = "fas fa-chart-line" if regime == "BULLISH" else "fas fa-minus" if regime == "NEUTRAL" else "fas fa-chart-line-down"
status_class = "status-bullish" if regime == "BULLISH" else "status-neutral" if regime == "NEUTRAL" else "status-bearish"
st.markdown(f"""
<div style="text-align: center;">
    <div class="market-status {status_class}">
        <i class="{status_icon}"></i> Market: {regime_msg} ({regime_score}/100)
    </div>
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
    # Professional signals header with icons
    count_text = f"{len(results)} Signal{'s' if len(results) > 1 else ''} Found"
    st.markdown(f'''
    <div class="signals-header">
        <span class="signals-count"><i class="fas fa-bullseye"></i> {count_text}</span>
        <span class="signals-subtitle">Take primary pick, rotate to next when position closed</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Premium capital input section
    st.markdown('''
    <div class="capital-section">
        <div class="capital-title"><i class="fas fa-wallet"></i> Trading Capital</div>
    </div>
    ''', unsafe_allow_html=True)
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
        card_class = "signal-card signal-primary" if i == 0 else "signal-card"
        
        # Sector icon mapping
        sector_icons = {
            "Technology": "fas fa-microchip",
            "Communication": "fas fa-satellite-dish",
            "Consumer": "fas fa-shopping-cart",
            "Healthcare": "fas fa-heartbeat",
            "Financial": "fas fa-university",
            "Industrial": "fas fa-industry",
            "Energy": "fas fa-bolt",
            "Materials": "fas fa-hammer"
        }
        sector_icon = sector_icons.get(result["sector"], "fas fa-building")
        
        # Build premium HTML card as single line
        card_html = f'<div class="{card_class}">'
        card_html += f'<div class="ticker-display">'
        card_html += f'<span class="ticker-symbol">{result["ticker"]}</span>'
        card_html += f'<span class="ticker-price">${ind["price"]:.2f}</span>'
        if i == 0:
            card_html += f'<span class="action-badge badge-primary"><i class="fas fa-star"></i> PRIMARY PICK</span>'
        else:
            card_html += f'<span class="action-badge badge-secondary"><i class="fas fa-clock"></i> ROTATION #{i+1}</span>'
        card_html += '</div>'
        card_html += f'<div class="sector-badge"><i class="{sector_icon}"></i> {result["sector"]}</div>'
        card_html += '<div class="metrics-grid" style="margin-top: 1.5rem;">'
        card_html += f'<div class="metric-card"><div class="metric-icon"><i class="fas fa-percentage text-purple"></i></div><div class="metric-value text-purple">{result["win_prob"]}%</div><div class="metric-label">Win Probability</div></div>'
        card_html += f'<div class="metric-card"><div class="metric-icon"><i class="fas fa-shield-alt text-bearish"></i></div><div class="metric-value text-bearish">${pos["sl"]:.2f}</div><div class="metric-label">Stop Loss ({pos["sl_pct"]:.1f}%)</div></div>'
        card_html += f'<div class="metric-card"><div class="metric-icon"><i class="fas fa-bullseye text-bullish"></i></div><div class="metric-value text-bullish">${pos["tp"]:.2f}</div><div class="metric-label">Target (+{pos["tp_pct"]:.1f}%)</div></div>'
        card_html += f'<div class="metric-card"><div class="metric-icon"><i class="fas fa-chart-bar text-cyan"></i></div><div class="metric-value text-cyan">{pos["shares"]:.0f}</div><div class="metric-label">Shares</div></div>'
        card_html += '</div>'
        card_html += f'<div class="trade-footer">'
        card_html += f'<span><i class="fas fa-arrow-down text-bearish"></i> Risk: <strong class="text-bearish">${pos["max_loss"]:.0f}</strong></span>'
        card_html += f'<span><i class="fas fa-arrow-up text-bullish"></i> Reward: <strong class="text-bullish">${pos["max_gain"]:.0f}</strong></span>'
        card_html += f'<span><i class="fas fa-balance-scale text-purple"></i> R:R <strong class="text-purple">1:{pos["rr"]:.1f}</strong></span>'
        card_html += '</div></div>'
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Expandable details for first signal only
        if i == 0:
            with st.expander("Why this stock?"):
                for title, text in reasons:
                    st.markdown(f'<div class="reason-item"><div class="reason-title">{title}</div><div class="reason-text">{text}</div></div>', unsafe_allow_html=True)
            
            with st.expander("View Chart"):
                fig = make_chart(result["df"], ind, pos)
                st.plotly_chart(fig, use_container_width=True)
    
    # Expected returns box
    avg_gain = 6.7
    avg_loss = 3.3
    win_rate = 0.45
    expected_per_trade = (win_rate * avg_gain) - ((1-win_rate) * avg_loss)
    monthly_trades = 7
    monthly_return = expected_per_trade * monthly_trades
    monthly_est = capital * monthly_return / 100
    
    returns_html = f'<div class="stats-container">'
    returns_html += '<div class="stats-title"><i class="fas fa-chart-line"></i> Expected Performance</div>'
    returns_html += '<div class="stats-grid">'
    returns_html += f'<div><div class="metric-icon"><i class="fas fa-calendar-alt"></i></div><div class="metric-value text-primary">~{monthly_trades}</div><div class="metric-label">TRADES/MONTH</div></div>'
    returns_html += f'<div><div class="metric-icon"><i class="fas fa-percentage"></i></div><div class="metric-value text-bullish">+{expected_per_trade:.1f}%</div><div class="metric-label">PER TRADE</div></div>'
    returns_html += f'<div><div class="metric-icon"><i class="fas fa-dollar-sign"></i></div><div class="metric-value text-bullish">+${monthly_est:.0f}</div><div class="metric-label">MONTHLY EST.</div></div>'
    returns_html += '</div>'
    returns_html += '<div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 1rem; text-align: center;">Based on ~45% win rate · +6.7% avg win · -3.3% avg loss</div>'
    returns_html += '</div>'
    st.markdown(returns_html, unsafe_allow_html=True)

elif scan_btn:
    st.markdown('<div class="empty-state"><div class="empty-icon"><i class="fas fa-search"></i></div><div class="empty-title">No Setups Found</div><div class="empty-text">Market conditions don\'t meet our 60%+ criteria right now. Try again tomorrow or adjust parameters.</div></div>', unsafe_allow_html=True)

else:
    ready_html = f'<div class="empty-state"><div class="empty-icon"><i class="fas fa-bullseye"></i></div><div class="empty-title">Ready to Scan</div><div class="empty-text">Scanning {len(ALL_TICKERS)} elite stocks for premium swing opportunities with 60%+ win probability and 2:1 reward/risk ratio</div></div>'
    st.markdown(ready_html, unsafe_allow_html=True)

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
            <div class="stats-container">
                <div class="stats-title"><i class="fas fa-history"></i> Backtest Results (3 Months)</div>
                <div class="stats-grid">
                    <div class="metric-card">
                        <div class="metric-icon"><i class="fas fa-bullseye"></i></div>
                        <div class="metric-value text-primary">{stats['total']}</div>
                        <div class="metric-label">Total Signals</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon"><i class="fas fa-trophy"></i></div>
                        <div class="metric-value text-bullish">{stats['win_rate']:.0f}%</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon"><i class="fas fa-arrow-up"></i></div>
                        <div class="metric-value text-bullish">+{stats['avg_win']:.1f}%</div>
                        <div class="metric-label">Avg Win</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon"><i class="fas fa-arrow-down"></i></div>
                        <div class="metric-value text-bearish">{stats['avg_loss']:.1f}%</div>
                        <div class="metric-label">Avg Loss</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div style="margin: 2rem 0; color: var(--text-secondary); font-weight: 600; font-size: 1.1rem;"><i class="fas fa-list"></i> Recent Signals</div>', unsafe_allow_html=True)
            
            for s in sorted(signals, key=lambda x: x["pnl_pct"], reverse=True)[:10]:
                result_color = "text-bullish" if s["won"] else "text-bearish"
                result_text = f"+{s['pnl_pct']:.1f}%" if s["won"] else f"{s['pnl_pct']:.1f}%"
                outcome_icon = "fas fa-bullseye" if s["hit_tp"] else "fas fa-shield-alt" if s["hit_sl"] else "fas fa-clock"
                outcome_text = "Target Hit" if s["hit_tp"] else "Stop Hit" if s["hit_sl"] else f"{s['days']} Days"
                
                st.markdown(f"""
                <div class="reason-item">
                    <div class="reason-title">
                        <span style="font-family: var(--font-mono); font-weight: 700;">{s['ticker']}</span>
                        <span class="metric-value {result_color}" style="font-size: 1rem;">{result_text}</span>
                    </div>
                    <div class="reason-text">
                        {s['date']} • Entry: ${s['entry']:.0f} → Exit: ${s['exit']:.0f} • 
                        <i class="{outcome_icon}"></i> {outcome_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon"><i class="fas fa-chart-line"></i></div>
                <div class="empty-title">No Historical Data</div>
                <div class="empty-text">No signals found in the past 3 months with current criteria</div>
            </div>
            """, unsafe_allow_html=True)
