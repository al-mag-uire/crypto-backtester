import streamlit as st
import pandas as pd
from datetime import datetime
from core.fetch import fetch_price, fetch_ohlcv
from core.paper_broker import PaperBroker
from core.indicators import compute_rsi
from streamlit_autorefresh import st_autorefresh
from typing import Dict, Any, Tuple

def initialize_broker() -> None:
    """Initialize the paper trading broker if not already in session state."""
    if 'paper_broker' not in st.session_state:
        st.session_state.paper_broker = PaperBroker(initial_balance=10000)

def get_trading_params() -> Tuple[Dict[str, Any], bool]:
    """Get trading parameters from the sidebar."""
    with st.sidebar.form("trading_params"):
        st.header("Trading Parameters")
        params = {
            "refresh_rate": st.slider("Refresh Rate (seconds)", 5, 60, 10),
            "rsi_period": st.slider("RSI Period", 5, 30, 14),
            "rsi_oversold": st.slider("RSI Oversold", 10, 40, 30),
            "rsi_overbought": st.slider("RSI Overbought", 60, 90, 70),
            "position_size": st.slider("Position Size (%)", 10, 100, 50) / 100,
            "stop_loss": st.slider("Stop Loss (%)", 1, 20, 5) / 100,
            "take_profit": st.slider("Take Profit (%)", 1, 50, 10) / 100
        }
        submitted = st.form_submit_button("Apply Settings")
        return params, submitted

def display_account_info(broker: PaperBroker, current_price: float) -> None:
    """Display account information and current positions."""
    # Account Overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Account Value", f"${broker.get_total_value(current_price):,.2f}")
    with col2:
        st.metric("Cash Balance", f"${broker.cash:,.2f}")
    with col3:
        pnl = broker.get_total_value(current_price) - 10000
        st.metric("Total P&L", f"${pnl:,.2f}", f"{(pnl/10000)*100:.1f}%")

    # Current Position
    if broker.position > 0:
        entry_price = broker.position_price
        unrealized_pnl = (current_price - entry_price) * broker.position
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        st.subheader("Current Position")
        pos_col1, pos_col2, pos_col3, pos_col4 = st.columns(4)
        with pos_col1:
            st.metric("Size", f"{broker.position:.4f}")
        with pos_col2:
            st.metric("Entry Price", f"${entry_price:.2f}")
        with pos_col3:
            st.metric("Unrealized P&L", f"${unrealized_pnl:.2f}")
        with pos_col4:
            st.metric("% Change", f"{pnl_pct:.1f}%")

def show_paper_trading():
    """Display the paper trading page."""
    st.header("💸 Paper Trading")
    
    # Initialize broker
    initialize_broker()
    broker = st.session_state.paper_broker
    
    # Coin selection
    coin_options = {
        "Bitcoin (BTC)": "bitcoin",
        "Ethereum (ETH)": "ethereum",
        "Solana (SOL)": "solana",
        "Cardano (ADA)": "cardano"
    }
    selected_coin = st.selectbox("Select Coin", list(coin_options.keys()))
    coin = coin_options[selected_coin]
    
    # Get parameters
    params, submitted = get_trading_params()
    
    # Auto-refresh counter
    count = st_autorefresh(interval=params['refresh_rate'] * 1000, key="trading_refresh")
    
    try:
        # Fetch latest data
        current_price = fetch_price(coin)
        df = fetch_ohlcv(coin, "usd", 1)  # Get last 24 hours of data
        
        if df.empty:
            st.error("Unable to fetch data. Please check your connection.")
            return
            
        # Display current price and time
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        with col2:
            st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))
        
        # Display account information
        display_account_info(broker, current_price)
        
        # Trading signals
        rsi = compute_rsi(df['close'], params['rsi_period'])
        current_rsi = rsi.iloc[-1]
        
        # Trading buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Buy", use_container_width=True):
                if broker.position == 0:  # Only buy if no position
                    position_size = broker.cash * params['position_size']
                    quantity = position_size / current_price
                    broker.open_position(quantity, current_price)
                    st.success(f"Bought {quantity:.4f} at ${current_price:.2f}")
        
        with col2:
            if st.button("Sell", use_container_width=True):
                if broker.position > 0:  # Only sell if position exists
                    quantity = broker.position
                    broker.close_position(current_price)
                    st.success(f"Sold {quantity:.4f} at ${current_price:.2f}")
        
        with col3:
            if st.button("Reset Account", use_container_width=True):
                st.session_state.paper_broker = PaperBroker(initial_balance=10000)
                st.experimental_rerun()
        
        # Trade History
        if broker.trade_history:
            st.subheader("Trade History")
            history_df = pd.DataFrame(broker.trade_history)
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            st.dataframe(history_df, use_container_width=True)
            
            # Calculate and display trade statistics
            total_trades = len(history_df)
            winning_trades = len(history_df[history_df['pnl'] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.metric("Total Trades", total_trades)
            with stats_col2:
                st.metric("Winning Trades", winning_trades)
            with stats_col3:
                st.metric("Win Rate", f"{win_rate:.1f}%")
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Error details:", e.__class__.__name__) 