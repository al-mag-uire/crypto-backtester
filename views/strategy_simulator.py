import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.fetch import fetch_ohlcv
from core.simulator import simulate_over_time, plot_price_and_equity
from strategies.ema import apply_ema_strategy
from strategies.rsi import apply_mean_reversion_strategy
from strategies.breakout import apply_breakout_strategy
from strategies.macd import apply_macd_strategy
from strategies.bollinger import apply_bollinger_strategy
from typing import Dict, Any, Tuple

def get_simulator_params() -> Tuple[Dict[str, Any], bool]:
    """Get simulation parameters from the sidebar."""
    with st.sidebar.form("simulator_params"):
        st.header("Simulation Parameters")
        
        params = {
            "initial_balance": st.number_input("Initial Balance ($)", 1000, 1000000, 10000),
            "position_size": st.slider("Position Size (%)", 10, 100, 50) / 100,
            "stop_loss": st.slider("Stop Loss (%)", 1, 20, 5) / 100,
            "take_profit": st.slider("Take Profit (%)", 1, 50, 10) / 100,
            "days": st.slider("Simulation Days", 30, 365, 90),
            "interval_hours": st.slider("Rebalance Interval (hours)", 1, 24, 4)
        }
        
        submitted = st.form_submit_button("Run Simulation")
        return params, submitted

def get_strategy_params(strategy: str) -> Dict[str, Any]:
    """Get strategy-specific parameters."""
    params = {}
    
    if strategy == "EMA":
        params.update({
            "fast": st.sidebar.slider("Fast EMA", 5, 50, 12),
            "slow": st.sidebar.slider("Slow EMA", 10, 100, 26),
            "rsi_period": st.sidebar.slider("RSI Period", 5, 30, 14),
            "rsi_threshold": st.sidebar.slider("RSI Buy Threshold", 10, 50, 30)
        })
    elif strategy == "RSI":
        params.update({
            "rsi_period": st.sidebar.slider("RSI Period", 5, 30, 14),
            "rsi_buy": st.sidebar.slider("RSI Buy", 10, 40, 30),
            "rsi_sell": st.sidebar.slider("RSI Sell", 60, 90, 70)
        })
    elif strategy == "Breakout":
        params.update({
            "window": st.sidebar.slider("Lookback Window", 5, 50, 20),
            "volatility_factor": st.sidebar.slider("Volatility Factor", 0.5, 2.0, 1.0, 0.1),
            "volume_factor": st.sidebar.slider("Volume Factor", 1.0, 3.0, 1.5, 0.1)
        })
    elif strategy == "MACD":
        params.update({
            "fast": st.sidebar.slider("MACD Fast", 5, 30, 12),
            "slow": st.sidebar.slider("MACD Slow", 10, 50, 26),
            "signal": st.sidebar.slider("Signal", 5, 20, 9)
        })
    elif strategy == "Bollinger Bands":
        params.update({
            "window": st.sidebar.slider("Window Length", 10, 50, 20),
            "num_std": st.sidebar.slider("# of Std Dev", 1, 3, 2)
        })
    
    return params

def show_strategy_simulator():
    """Display the strategy simulator page."""
    st.header("📈 Strategy Simulator")
    
    # Strategy selection
    strategy_options = ["EMA", "RSI", "Breakout", "MACD", "Bollinger Bands"]
    strategy = st.selectbox("Select Strategy", strategy_options)
    
    # Coin selection
    coin_options = {
        "Bitcoin (BTC)": "bitcoin",
        "Ethereum (ETH)": "ethereum",
        "Solana (SOL)": "solana",
        "Cardano (ADA)": "cardano"
    }
    selected_coin = st.selectbox("Select Coin", list(coin_options.keys()))
    coin = coin_options[selected_coin]
    
    # Get simulation and strategy parameters
    sim_params, submitted = get_simulator_params()
    strategy_params = get_strategy_params(strategy)
    
    if submitted:
        with st.spinner("Running simulation..."):
            try:
                # Fetch data
                df = fetch_ohlcv(coin, "usd", sim_params["days"])
                
                if df.empty:
                    st.error("Unable to fetch data. Please check your connection.")
                    return
                
                # Map strategy functions
                strategy_funcs = {
                    "EMA": apply_ema_strategy,
                    "RSI": apply_mean_reversion_strategy,
                    "Breakout": apply_breakout_strategy,
                    "MACD": apply_macd_strategy,
                    "Bollinger": apply_bollinger_strategy
                }
                
                # Run simulation
                results = simulate_over_time(
                    df=df,
                    strategy_func=strategy_funcs[strategy],
                    strategy_params=strategy_params,
                    initial_balance=sim_params["initial_balance"],
                    position_size=sim_params["position_size"],
                    stop_loss=sim_params["stop_loss"],
                    take_profit=sim_params["take_profit"],
                    interval_hours=sim_params["interval_hours"]
                )
                
                # Display results
                final_equity = results["equity"].iloc[-1]
                total_return = (final_equity - sim_params["initial_balance"]) / sim_params["initial_balance"] * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Final Equity", f"${final_equity:,.2f}")
                with col2:
                    st.metric("Total Return", f"{total_return:.1f}%")
                with col3:
                    st.metric("Total Trades", len(results[results["trade_type"].notna()]))
                
                # Plot results
                fig = plot_price_and_equity(results)
                st.pyplot(fig)
                
                # Trade Analysis
                st.subheader("Trade Analysis")
                trades = results[results["trade_type"].notna()].copy()
                trades["pnl"] = trades["trade_pnl"].fillna(0)
                
                winning_trades = len(trades[trades["pnl"] > 0])
                losing_trades = len(trades[trades["pnl"] <= 0])
                win_rate = winning_trades / len(trades) * 100 if len(trades) > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Winning Trades", winning_trades)
                with col2:
                    st.metric("Losing Trades", losing_trades)
                with col3:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                # Display trade history
                st.subheader("Trade History")
                trade_history = trades[["timestamp", "trade_type", "price", "pnl"]].copy()
                trade_history.columns = ["Timestamp", "Action", "Price", "PnL"]
                st.dataframe(trade_history, use_container_width=True)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.write("Error details:", e.__class__.__name__) 