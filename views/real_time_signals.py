import streamlit as st
from datetime import datetime
import pandas as pd
from core.fetch import fetch_price, fetch_ohlcv
from core.indicators import compute_rsi
from streamlit_autorefresh import st_autorefresh
from typing import Dict, Any

def get_signal_params() -> Dict[str, Any]:
    """Get signal parameters from the sidebar."""
    with st.sidebar.form("signal_params"):
        st.header("Signal Parameters")
        params = {
            "refresh_rate": st.slider("Refresh Rate (seconds)", 5, 60, 10),
            "rsi_period": st.slider("RSI Period", 5, 30, 14),
            "rsi_oversold": st.slider("RSI Oversold", 10, 40, 30),
            "rsi_overbought": st.slider("RSI Overbought", 60, 90, 70),
            "ema_fast": st.slider("Fast EMA", 5, 50, 12),
            "ema_slow": st.slider("Slow EMA", 10, 100, 26)
        }
        submitted = st.form_submit_button("Apply Settings")
        return params, submitted

def analyze_signals(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze current market signals."""
    current_price = df['close'].iloc[-1]
    
    # RSI Analysis
    rsi = compute_rsi(df['close'], params['rsi_period'])
    current_rsi = rsi.iloc[-1]
    rsi_signal = "Oversold" if current_rsi < params['rsi_oversold'] else \
                 "Overbought" if current_rsi > params['rsi_overbought'] else "Neutral"
    
    # EMA Analysis
    df['ema_fast'] = df['close'].ewm(span=params['ema_fast']).mean()
    df['ema_slow'] = df['close'].ewm(span=params['ema_slow']).mean()
    ema_fast_current = df['ema_fast'].iloc[-1]
    ema_slow_current = df['ema_slow'].iloc[-1]
    ema_signal = "Bullish" if ema_fast_current > ema_slow_current else "Bearish"
    
    # Volume Analysis
    avg_volume = df['volume'].mean()
    current_volume = df['volume'].iloc[-1]
    volume_signal = "High" if current_volume > avg_volume * 1.5 else \
                   "Low" if current_volume < avg_volume * 0.5 else "Normal"
    
    return {
        "price": current_price,
        "rsi": current_rsi,
        "rsi_signal": rsi_signal,
        "ema_signal": ema_signal,
        "volume_signal": volume_signal,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

def show_real_time_signals():
    """Display the real-time signals page."""
    st.header("🔔 Real-Time Trading Signals")
    
    # Get coin selection
    coin_options = {
        "Bitcoin (BTC)": "bitcoin",
        "Ethereum (ETH)": "ethereum",
        "Solana (SOL)": "solana",
        "Cardano (ADA)": "cardano"
    }
    selected_coin = st.selectbox("Select Coin", list(coin_options.keys()))
    coin = coin_options[selected_coin]
    
    # Get parameters
    params, submitted = get_signal_params()
    
    # Auto-refresh counter
    count = st_autorefresh(interval=params['refresh_rate'] * 1000, key="signal_refresh")
    
    try:
        # Fetch latest data
        df = fetch_ohlcv(coin, "usd", 1)  # Get last 24 hours of data
        if df.empty:
            st.error("Unable to fetch data. Please check your connection.")
            return
            
        # Analyze signals
        signals = analyze_signals(df, params)
        
        # Display current price and time
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Price", f"${signals['price']:.2f}")
        with col2:
            st.metric("Last Update", signals['timestamp'])
        
        # Display signals
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("RSI", f"{signals['rsi']:.1f}")
            color = ("🔴" if signals['rsi_signal'] == "Overbought" else 
                    "🟢" if signals['rsi_signal'] == "Oversold" else "⚪")
            st.write(f"{color} RSI Signal: {signals['rsi_signal']}")
            
        with col2:
            st.metric("EMA Signal", signals['ema_signal'])
            color = "🟢" if signals['ema_signal'] == "Bullish" else "🔴"
            st.write(f"{color} Trend: {signals['ema_signal']}")
            
        with col3:
            st.metric("Volume", signals['volume_signal'])
            color = ("🟢" if signals['volume_signal'] == "High" else 
                    "🔴" if signals['volume_signal'] == "Low" else "⚪")
            st.write(f"{color} Volume: {signals['volume_signal']}")
        
        # Display signal history
        if 'signal_history' not in st.session_state:
            st.session_state.signal_history = []
            
        # Add current signals to history
        st.session_state.signal_history.append(signals)
        
        # Keep only last 100 signals
        if len(st.session_state.signal_history) > 100:
            st.session_state.signal_history.pop(0)
        
        # Display history as table
        if st.session_state.signal_history:
            st.subheader("Signal History")
            history_df = pd.DataFrame(st.session_state.signal_history)
            st.dataframe(history_df, use_container_width=True)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Error details:", e.__class__.__name__) 