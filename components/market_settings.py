import streamlit as st
from datetime import datetime
import uuid

def get_market_settings():
    """Get market settings from sidebar"""
    
    # Generate a unique ID for this session if not exists
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    st.sidebar.markdown("### Strategy Settings")
    
    # Use session ID in keys to make them unique
    strategy = st.sidebar.selectbox(
        "Choose Strategy",
        ["RSI Mean Reversion", "EMA Crossover", "MACD", "Bollinger Bands"],
        key=f"strategy_{st.session_state.session_id}"
    )
    
    testing_mode = st.sidebar.checkbox(
        "Testing Mode (Mock Data)", 
        value=True,
        help="Use mock data to avoid API rate limits",
        key=f"testing_{st.session_state.session_id}"
    )
    
    st.sidebar.markdown("### Market Settings")
    
    coin = st.sidebar.selectbox(
        "Select Coin",
        ["Bitcoin (BTC)", "Ethereum (ETH)", "Binance Coin (BNB)"],
        key=f"coin_{st.session_state.session_id}"
    ).split()[0].lower()
    
    vs_currency = st.sidebar.text_input(
        "Quote Currency",
        value="usd",
        key=f"currency_{st.session_state.session_id}"
    ).lower()
    
    days = st.sidebar.slider(
        "Number of Days",
        min_value=10,
        max_value=90,
        value=30,
        key=f"days_{st.session_state.session_id}"
    )
    
    strategy_params = {}
    if strategy == "RSI Mean Reversion":
        st.sidebar.markdown("### Strategy Parameters")
        
        rsi_period = st.sidebar.slider(
            "RSI Period", 
            5, 30, 14, 
            key=f"rsi_period_{st.session_state.session_id}"
        )
        rsi_buy = st.sidebar.slider(
            "RSI Buy Level", 
            10, 40, 30, 
            key=f"rsi_buy_{st.session_state.session_id}"
        )
        rsi_sell = st.sidebar.slider(
            "RSI Sell Level", 
            60, 90, 70, 
            key=f"rsi_sell_{st.session_state.session_id}"
        )
        
        strategy_params = {
            "rsi_period": rsi_period,
            "rsi_buy": rsi_buy,
            "rsi_sell": rsi_sell
        }
    
    st.sidebar.markdown("---")
    run_backtest = st.sidebar.button(
        "Run Backtest",
        type="primary",
        use_container_width=True,
        key=f"run_{st.session_state.session_id}"
    )
    
    return {
        "strategy": strategy,
        "coin": coin,
        "vs_currency": vs_currency,
        "days": days,
        "testing_mode": testing_mode,
        "strategy_params": strategy_params,
        "run_backtest": run_backtest
    }
