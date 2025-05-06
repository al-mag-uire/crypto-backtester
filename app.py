import streamlit as st
import pandas as pd
from datetime import datetime

# Core utils
from core.backtest import (
    backtest, run_backtest,
    COIN_ID, VS_CURRENCY, DAYS,
    EMA_FAST, EMA_SLOW,
    RSI_PERIOD, RSI_BUY_THRESHOLD,
    INITIAL_BALANCE, STOP_LOSS_PCT, TAKE_PROFIT_PCT
)
from core.indicators import compute_rsi

# Strategy functions
from strategies.ema import apply_ema_strategy
from strategies.rsi import apply_mean_reversion_strategy 
from strategies.breakout import apply_breakout_strategy
from strategies.macd import apply_macd_strategy
from strategies.bollinger import apply_bollinger_strategy

# Import components
from components.performance_metrics import show_performance_table, show_equity_curve

# Import views
from views.strategy_backtest import show_strategy_backtest
from views.screener import show_screener
from views.real_time_signals import show_real_time_signals
from views.paper_trading import show_paper_trading
from views.strategy_simulator import show_strategy_simulator
from views.multi_backtest import show_multi_backtest

# Import utils
from utils.styles import load_css

# Initialize session state for parameters if not exists
if 'params' not in st.session_state:
    st.session_state.params = {
        'strategy': None,
        'testing_mode': True,
        'coin': None,
        'currency': 'usd',
        'days': 30,
        'strategy_params': {}
    }

# Page config
st.set_page_config(page_title="Crypto Trading Bot", page_icon="🤖", layout="wide")
load_css()
st.title("🤖 Crypto Trading Bot")

# Main Navigation
navigation = st.sidebar.radio(
    "Main Navigation",
    ["Strategy Testing & Backtesting", "Market Screener", "Paper Trading"]
)

if navigation == "Strategy Testing & Backtesting":
    tool = st.sidebar.selectbox(
        "Select Tool",
        ["Single Strategy Backtest", "Multi-Asset Backtest"]
    )
    
    if tool == "Single Strategy Backtest":
        # Strategy selection
        st.session_state.params['strategy'] = st.sidebar.selectbox(
            "Choose Strategy", 
            ["RSI Mean Reversion", "EMA Crossover", "MACD", "Bollinger Bands", "Breakout"]
        )
        
        # Market Settings
        st.sidebar.markdown("### Strategy Settings")
        
        st.session_state.params['testing_mode'] = st.sidebar.checkbox(
            "Testing Mode (Mock Data)", 
            value=True, 
            key="testing_mode_checkbox"
        )
        
        # Only show market settings for strategies that need them
        if st.session_state.params['strategy'] in ["RSI Mean Reversion", "EMA Crossover", "MACD", "Bollinger Bands", "Breakout"]:
            st.sidebar.markdown("### Market Settings")
            st.session_state.params['coin'] = st.sidebar.selectbox(
                "Select Coin", 
                ["Bitcoin (BTC)", "Ethereum (ETH)"],
                key="coin_selector"
            ).split()[0].lower()
            
            st.session_state.params['currency'] = st.sidebar.text_input(
                "Quote Currency", 
                value="usd",
                key="currency_input"
            ).lower()
            
            st.session_state.params['days'] = st.sidebar.slider(
                "Number of Days", 
                10, 90, 30,
                key="days_slider"
            )
            
            # Strategy specific parameters
            st.sidebar.markdown("### Strategy Parameters")
            
            if st.session_state.params['strategy'] == "RSI Mean Reversion":
                rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14, key="rsi_period")
                rsi_buy = st.sidebar.slider("RSI Buy Level", 10, 40, 30, key="rsi_buy")
                rsi_sell = st.sidebar.slider("RSI Sell Level", 60, 90, 70, key="rsi_sell")
                st.session_state.params['strategy_params'] = {
                    "rsi_period": rsi_period,
                    "rsi_buy": rsi_buy,
                    "rsi_sell": rsi_sell
                }
            elif st.session_state.params['strategy'] == "EMA Crossover":
                fast = st.sidebar.slider("Fast EMA", 5, 50, 12, key="fast_ema")
                slow = st.sidebar.slider("Slow EMA", 10, 100, 26, key="slow_ema")
                rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14, key="rsi_period")
                rsi_oversold = st.sidebar.slider("RSI Oversold", 10, 40, 30, key="rsi_oversold")
                rsi_overbought = st.sidebar.slider("RSI Overbought", 60, 90, 70, key="rsi_overbought")
                st.session_state.params['strategy_params'] = {
                    "fast": fast,
                    "slow": slow,
                    "rsi_period": rsi_period,
                    "rsi_oversold": rsi_oversold,
                    "rsi_overbought": rsi_overbought
                }
            elif st.session_state.params['strategy'] == "MACD":
                fast = st.sidebar.slider("Fast Period", 5, 30, 12, key="macd_fast")
                slow = st.sidebar.slider("Slow Period", 10, 50, 26, key="macd_slow")
                signal = st.sidebar.slider("Signal Period", 5, 20, 9, key="macd_signal")
                st.session_state.params['strategy_params'] = {
                    "fast": fast,
                    "slow": slow,
                    "signal": signal
                }
            elif st.session_state.params['strategy'] == "Bollinger Bands":
                window = st.sidebar.slider("Window Length", 10, 50, 20, key="bb_window")
                num_std = st.sidebar.slider("Number of Standard Deviations", 1, 3, 2, key="bb_std")
                st.session_state.params['strategy_params'] = {
                    "window": window,
                    "num_std": num_std
                }
                
            elif st.session_state.params['strategy'] == "Breakout":
                window = st.sidebar.slider("Lookback Window", 5, 50, 20, key="breakout_window")
                volatility_factor = st.sidebar.slider("Volatility Factor", 0.5, 2.0, 1.0, 0.1, key="volatility_factor")
                volume_factor = st.sidebar.slider("Volume Factor", 1.0, 3.0, 1.5, 0.1, key="volume_factor")
                st.session_state.params['strategy_params'] = {
                    "window": window,
                    "volatility_factor": volatility_factor,
                    "volume_factor": volume_factor
                }
        
        # Run button
        should_run = st.sidebar.button("Run Backtest", type="primary")
        
        if should_run:
            # Map strategy names to their internal identifiers
            strategy_map = {
                "RSI Mean Reversion": "rsi",
                "EMA Crossover": "ema",
                "MACD": "macd",
                "Bollinger Bands": "bollinger",
                "Breakout": "breakout"
            }
            
            show_strategy_backtest(
                strategy=strategy_map[st.session_state.params['strategy']],
                coin=st.session_state.params['coin'],
                vs_currency=st.session_state.params['currency'],
                days=st.session_state.params['days'],
                testing_mode=st.session_state.params['testing_mode'],
                strategy_params=st.session_state.params['strategy_params'],
                should_run_backtest=should_run
            )
    elif tool == "Multi-Asset Backtest":
        show_multi_backtest()

elif navigation == "Market Screener":
    show_screener()

elif navigation == "Paper Trading":
    show_paper_trading()