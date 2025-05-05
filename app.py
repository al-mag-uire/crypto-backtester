import streamlit as st
import pandas as pd
from datetime import datetime

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

# Single sidebar with all settings
with st.sidebar:
    st.markdown("### Strategy Settings")
    
    # Store strategy selection in session state
    st.session_state.params['strategy'] = st.selectbox(
        "Choose Strategy", 
        [
            "RSI Mean Reversion",
            "EMA Crossover",
            "MACD",
            "Bollinger Bands",
            "Breakout"
        ],
        key="strategy_selector"
    )
    
    st.session_state.params['testing_mode'] = st.checkbox(
        "Testing Mode (Mock Data)", 
        value=True, 
        key="testing_mode_checkbox"
    )
    
    # Only show market settings for strategies that need them
    if st.session_state.params['strategy'] in ["RSI Mean Reversion", "EMA Crossover", "MACD", "Bollinger Bands", "Breakout"]:
        st.markdown("### Market Settings")
        st.session_state.params['coin'] = st.selectbox(
            "Select Coin", 
            ["Bitcoin (BTC)", "Ethereum (ETH)"],
            key="coin_selector"
        ).split()[0].lower()
        
        st.session_state.params['currency'] = st.text_input(
            "Quote Currency", 
            value="usd",
            key="currency_input"
        ).lower()
        
        st.session_state.params['days'] = st.slider(
            "Number of Days", 
            10, 90, 30,
            key="days_slider"
        )
        
        # Strategy specific parameters
        st.markdown("### Strategy Parameters")
        
        if st.session_state.params['strategy'] == "RSI Mean Reversion":
            rsi_period = st.slider("RSI Period", 5, 30, 14, key="rsi_period")
            rsi_buy = st.slider("RSI Buy Level", 10, 40, 30, key="rsi_buy")
            rsi_sell = st.slider("RSI Sell Level", 60, 90, 70, key="rsi_sell")
            st.session_state.params['strategy_params'] = {
                "rsi_period": rsi_period,
                "rsi_buy": rsi_buy,
                "rsi_sell": rsi_sell
            }
        elif st.session_state.params['strategy'] == "EMA Crossover":
            fast = st.slider("Fast EMA", 5, 50, 12, key="fast_ema")
            slow = st.slider("Slow EMA", 10, 100, 26, key="slow_ema")
            rsi_period = st.slider("RSI Period", 5, 30, 14, key="rsi_period")
            rsi_threshold = st.slider("RSI Buy Threshold", 10, 50, 30, key="rsi_threshold")
            st.session_state.params['strategy_params'] = {
                "fast": fast,
                "slow": slow,
                "rsi_period": rsi_period,
                "rsi_threshold": rsi_threshold
            }
        elif st.session_state.params['strategy'] == "MACD":
            fast = st.slider("Fast Period", 5, 30, 12, key="macd_fast")
            slow = st.slider("Slow Period", 10, 50, 26, key="macd_slow")
            signal = st.slider("Signal Period", 5, 20, 9, key="macd_signal")
            st.session_state.params['strategy_params'] = {
                "fast": fast,
                "slow": slow,
                "signal": signal
            }
        elif st.session_state.params['strategy'] == "Bollinger Bands":
            window = st.slider("Window Length", 10, 50, 20, key="bb_window")
            num_std = st.slider("Number of Standard Deviations", 1, 3, 2, key="bb_std")
            st.session_state.params['strategy_params'] = {
                "window": window,
                "num_std": num_std
            }
            
        elif st.session_state.params['strategy'] == "Breakout":
            window = st.slider("Lookback Window", 5, 50, 20, key="breakout_window")
            st.session_state.params['strategy_params'] = {
                "window": window
            }
    
    # Run button
    should_run = st.button("Run Backtest", type="primary", key="run_button")

# Main content area
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
else:
    st.info("👈 Adjust your parameters and click 'Run Backtest' to start")