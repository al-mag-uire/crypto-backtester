import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any
from datetime import datetime

from core.fetch import fetch_ohlcv
from core.backtest import run_backtest
from components.performance_metrics import show_performance_table, show_equity_curve
from utils.chart_utils import plot_strategy_indicators
from strategies.ema import apply_ema_strategy
from strategies.rsi import apply_mean_reversion_strategy
from strategies.breakout import apply_breakout_strategy
from strategies.macd import apply_macd_strategy
from strategies.bollinger import apply_bollinger_strategy

def show_strategy_backtest(strategy: str, coin: str, vs_currency: str, days: int, testing_mode: bool, strategy_params: dict, should_run_backtest: bool) -> None:
    """Show strategy backtest page."""
    
    if not should_run_backtest:
        st.info("👈 Adjust your parameters and click 'Run Backtest' to start")
        return
        
    try:
        # Fetch data
        df = fetch_ohlcv(coin, vs_currency, days, testing_mode=testing_mode)
        
        if df.empty:
            st.error("Unable to fetch data. Please check your connection.")
            return
        
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Get strategy parameters and apply strategy
            if strategy == "rsi":
                df = apply_mean_reversion_strategy(
                    df=df,
                    **strategy_params
                )
            
            elif strategy == "ema":
                # Update parameter names for EMA strategy
                updated_params = {
                    'fast': strategy_params.get('fast', 12),
                    'slow': strategy_params.get('slow', 26),
                    'rsi_period': strategy_params.get('rsi_period', 14),
                    'rsi_oversold': strategy_params.get('rsi_oversold', 30),
                    'rsi_overbought': strategy_params.get('rsi_overbought', 70)
                }
                df = apply_ema_strategy(
                    df=df,
                    **updated_params
                )
            
            elif strategy == "breakout":
                df = apply_breakout_strategy(
                    df=df,
                    **strategy_params
                )
            
            elif strategy == "macd":
                df = apply_macd_strategy(
                    df=df,
                    **strategy_params
                )
            
            elif strategy == "bollinger":
                df = apply_bollinger_strategy(
                    df=df,
                    **strategy_params
                )
        
        # Run backtest with the strategy signals
        results = run_backtest(
            df=df,
            strategy_func=lambda x: x['signal'],
            strategy_params={},  # Parameters already applied in strategy function
            initial_capital=10000,
            position_size=0.5,
            stop_loss=0.05,
            take_profit=0.1
        )
        
        # Add this section to show the strategy chart
        st.subheader("Strategy Chart")
        plot_strategy_indicators(df, strategy)
        
        # Show performance metrics
        st.subheader("Performance Summary")
        show_performance_table(results['results'])
        
        # Show equity curve
        st.subheader("Equity Curve")
        show_equity_curve(results['results'])
        
        # Show trade history in an expandable section
        with st.expander("Trade History", expanded=False):
            trades_df = results['trades']
            if not trades_df.empty:
                # Calculate trade returns
                trades_df['return'] = trades_df['capital'].pct_change()
                
                # Format the trades dataframe
                trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                trades_df['price'] = trades_df['price'].round(2)
                trades_df['capital'] = trades_df['capital'].round(2)
                trades_df['return'] = (trades_df['return'] * 100).round(2)
                
                # Add return color formatting
                def color_returns(val):
                    color = 'green' if val > 0 else 'red' if val < 0 else 'white'
                    return f'color: {color}'
                
                st.dataframe(
                    trades_df.style.applymap(
                        color_returns, 
                        subset=['return']
                    ),
                    use_container_width=True
                )
            else:
                st.info("No trades executed during this period")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Error details:", type(e).__name__)

def plot_strategy_charts(df: pd.DataFrame, trades_df: pd.DataFrame, strategy: str) -> None:
    """Plot strategy-specific charts."""
    if strategy == "ema":
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, 
                                      gridspec_kw={"height_ratios": [3, 1]})
        
        # Price and EMAs
        ax1.plot(df["timestamp"], df["close"], label="Price")
        ax1.plot(df["timestamp"], df["ema_fast"], label="Fast EMA")
        ax1.plot(df["timestamp"], df["ema_slow"], label="Slow EMA")
        
        # Plot trades
        for i, row in trades_df.iterrows():
            if "BUY" in row["action"]:
                ax1.scatter(row["timestamp"], row["price"], marker="^", color="limegreen", 
                          label="Buy" if i == 0 else "", s=100, edgecolor="black")
            elif "SELL" in row["action"]:
                ax1.scatter(row["timestamp"], row["price"], marker="v", color="crimson", 
                          label="Sell" if i == 0 else "", s=100, edgecolor="black")
        ax1.legend()
        ax1.set_title("Trade Chart")
        
        # RSI
        ax2.plot(df["timestamp"], df["rsi"], label="RSI", color="purple")
        ax2.axhline(30, color="red", linestyle="--", label="RSI 30")
        ax2.axhline(70, color="green", linestyle="--", label="RSI 70")
        ax2.set_ylim(0, 100)
        ax2.set_title("RSI")
        ax2.legend()
        
        st.pyplot(fig)
    
    elif strategy == "macd":
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, 
                                      gridspec_kw={"height_ratios": [3, 1]})
        
        # Price chart
        ax1.plot(df["timestamp"], df["close"], label="Price", color='blue', alpha=0.8)
        
        # Plot trades
        for i, row in trades_df.iterrows():
            if "BUY" in row["action"]:
                ax1.scatter(row["timestamp"], row["price"], marker="^", color="limegreen", 
                          label="Buy" if i == 0 else "", s=100, edgecolor="black")
            elif "SELL" in row["action"]:
                ax1.scatter(row["timestamp"], row["price"], marker="v", color="crimson", 
                          label="Sell" if i == 0 else "", s=100, edgecolor="black")
        ax1.legend()
        ax1.set_title("Price and Trades")
        ax1.grid(True, alpha=0.2)
        
        # MACD
        ax2.plot(df["timestamp"], df["macd"], label="MACD", color='blue')
        ax2.plot(df["timestamp"], df["macd_signal"], label="Signal", color='orange')
        ax2.bar(df["timestamp"], df["hist"], label="Histogram", color='gray', alpha=0.3)
        ax2.axhline(0, color='black', linestyle='--', alpha=0.3)
        ax2.set_title("MACD")
        ax2.grid(True, alpha=0.2)
        ax2.legend()
        
        plt.tight_layout()

    # Add other strategy-specific plots here...
