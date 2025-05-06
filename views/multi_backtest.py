import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from core.multi_backtest import run_multi_backtest
from strategies.ema import apply_ema_strategy
from strategies.rsi import apply_mean_reversion_strategy
from strategies.breakout import apply_breakout_strategy
from strategies.macd import apply_macd_strategy
from strategies.bollinger import apply_bollinger_strategy
from typing import Dict, Any, Tuple, List

def get_multi_backtest_params() -> Tuple[Dict[str, Any], bool]:
    """Get multi-backtest parameters from the sidebar."""
    with st.sidebar.form("multi_backtest_params"):
        st.header("Backtest Parameters")
        params = {
            "initial_balance": st.number_input("Initial Balance ($)", 1000, 1000000, 10000),
            "position_size": st.slider("Position Size per Coin (%)", 10, 100, 20) / 100,
            "stop_loss": st.slider("Stop Loss (%)", 1, 20, 5) / 100,
            "take_profit": st.slider("Take Profit (%)", 1, 50, 10) / 100,
            "days": st.slider("Backtest Days", 30, 365, 90),
            "rebalance_days": st.slider("Rebalance Every N Days", 1, 30, 7)
        }
        submitted = st.form_submit_button("Run Backtest")
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
    elif strategy == "MACD":
        params.update({
            "fast": st.sidebar.slider("MACD Fast", 5, 30, 12),
            "slow": st.sidebar.slider("MACD Slow", 10, 50, 26),
            "signal": st.sidebar.slider("Signal", 5, 20, 9)
        })
    elif strategy == "Bollinger":
        params.update({
            "window": st.sidebar.slider("Window Length", 10, 50, 20),
            "num_std": st.sidebar.slider("Number of Std Dev", 1, 3, 2)
        })
    elif strategy == "Breakout":
        params.update({
            "window": st.sidebar.slider("Lookback Window", 5, 50, 20)
        })
    
    return params

def plot_portfolio_performance(results: pd.DataFrame) -> None:
    """Plot portfolio equity curve and drawdown."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # Equity curve
    ax1.plot(results.index, results['total_equity'], label='Portfolio Value')
    ax1.set_title('Portfolio Performance')
    ax1.legend()
    ax1.grid(True)
    
    # Drawdown
    drawdown = (results['total_equity'] / results['total_equity'].cummax() - 1) * 100
    ax2.fill_between(results.index, drawdown, 0, color='red', alpha=0.3)
    ax2.set_title('Drawdown (%)')
    ax2.grid(True)
    
    st.pyplot(fig)

def show_performance_comparison(results: Dict[str, Any]) -> None:
    """Display performance comparison table for all coins"""
    # Prepare metrics for each coin
    metrics = []
    
    for coin, data in results.items():
        if coin != 'portfolio':  # Skip portfolio metrics for this table
            metrics.append({
                'Coin': coin.upper(),
                'Return %': f"{data['return_pct']:.2f}%",
                'Final Balance': f"${data['final_balance']:,.2f}",
                'Win Rate': f"{data['win_rate']:.1f}%",
                'Sharpe Ratio': f"{data['sharpe_ratio']:.2f}",
                'PnL': f"${data['pnl']:,.2f}",
                'Trades': len(data['trades'])
            })
    
    # Convert to DataFrame and display
    df_metrics = pd.DataFrame(metrics)
    df_metrics.set_index('Coin', inplace=True)
    st.table(df_metrics)

def plot_equity_curves(results: Dict[str, Any]) -> None:
    """Plot equity curves for all coins and portfolio"""
    fig = go.Figure()
    
    # Plot individual coin equity curves
    for coin, data in results.items():
        if coin != 'portfolio':
            fig.add_trace(go.Scatter(
                y=data['equity_curve'],
                name=coin.upper(),
                mode='lines',
                line=dict(width=1),
                opacity=0.7
            ))
    
    # Plot portfolio equity curve
    if 'portfolio' in results:
        fig.add_trace(go.Scatter(
            y=results['portfolio']['equity_curve'],
            name='Portfolio Total',
            mode='lines',
            line=dict(width=2, color='black'),
            opacity=1
        ))
    
    fig.update_layout(
        title='Equity Curves Comparison',
        xaxis_title='Time',
        yaxis_title='Equity ($)',
        height=600,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_drawdown_analysis(results: Dict[str, Any]) -> None:
    """Plot drawdown analysis for all coins"""
    fig = go.Figure()
    
    for coin, data in results.items():
        if coin != 'portfolio':
            # Calculate drawdown series
            equity = data['equity_curve']
            drawdown = (equity / equity.cummax() - 1) * 100
            
            fig.add_trace(go.Scatter(
                y=drawdown,
                name=coin.upper(),
                mode='lines',
                line=dict(width=1),
                opacity=0.7
            ))
    
    fig.update_layout(
        title='Drawdown Analysis',
        xaxis_title='Time',
        yaxis_title='Drawdown (%)',
        height=400,
        showlegend=True,
        yaxis_tickformat='%'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def calculate_correlation_matrix(results: Dict[str, Any]) -> pd.DataFrame:
    """Calculate correlation matrix between coin returns"""
    # Extract returns for each coin
    returns = {}
    for coin, data in results.items():
        if coin != 'portfolio':
            returns[coin.upper()] = data['equity_curve'].pct_change()
    
    # Create correlation matrix
    return pd.DataFrame(returns).corr()

def show_multi_backtest():
    """Display the multi-asset backtest page"""
    st.header("📊 Multi-Asset Backtest")
    
    # Sidebar inputs
    with st.sidebar:
        st.subheader("Backtest Parameters")
        
        # Strategy selection
        strategy = st.selectbox(
            "Select Strategy",
            ["ema", "rsi", "macd", "bollinger", "breakout"],
            format_func=lambda x: x.upper()
        )
        
        # Coin selection
        coins = st.multiselect(
            "Select Coins",
            ["bitcoin", "ethereum", "solana", "cardano", "binancecoin"],
            default=["bitcoin", "ethereum"],
            format_func=lambda x: x.upper()
        )
        
        # Basic parameters
        days = st.slider("Backtest Days", 30, 365, 90)
        initial_balance = st.number_input("Initial Balance ($)", 1000, 1000000, 10000)
        position_size = st.slider("Position Size per Coin (%)", 1, 100, 20) / 100
        stop_loss = st.slider("Stop Loss (%)", 1, 50, 5) / 100
        take_profit = st.slider("Take Profit (%)", 1, 50, 10) / 100
        rebalance_days = st.slider("Rebalance Days", 1, 30, 7)
        
        # Strategy-specific parameters
        st.subheader("Strategy Parameters")
        strategy_params = {}
        
        if strategy == "ema":
            strategy_params = {
                "fast": st.slider("Fast EMA", 5, 50, 12),
                "slow": st.slider("Slow EMA", 10, 200, 26),
                "rsi_period": st.slider("RSI Period", 5, 30, 14),
                "rsi_threshold": st.slider("RSI Threshold", 10, 40, 30)
            }
        elif strategy == "rsi":
            strategy_params = {
                "rsi_period": st.slider("RSI Period", 5, 30, 14),
                "rsi_buy": st.slider("RSI Buy Level", 10, 40, 30),
                "rsi_sell": st.slider("RSI Sell Level", 60, 90, 70)
            }
        # Add parameters for other strategies as needed
        
        run_test = st.button("Run Backtest", type="primary")
    
    # Main content area
    if run_test and coins:
        with st.spinner("Running backtest..."):
            results = run_multi_backtest(
                coins=coins,
                strategy=strategy,
                days=days,
                initial_balance=initial_balance,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                rebalance_days=rebalance_days,
                strategy_params=strategy_params
            )
            
            if results:
                # Portfolio Summary
                st.subheader("Portfolio Summary")
                portfolio_metrics = results['portfolio']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Portfolio Return", 
                             f"{portfolio_metrics['return_pct']:.2f}%")
                with col2:
                    st.metric("Final Balance", 
                             f"${portfolio_metrics['final_balance']:,.2f}")
                with col3:
                    st.metric("Max Drawdown", 
                             f"{portfolio_metrics['max_drawdown_pct']:.2f}%")
                
                # Individual Coin Performance
                st.subheader("Coin Performance Comparison")
                show_performance_comparison(results)
                
                # Equity Curves
                st.subheader("Equity Curves")
                plot_equity_curves(results)
                
                # Drawdown Analysis
                st.subheader("Drawdown Analysis")
                plot_drawdown_analysis(results)
                
                # Correlation Matrix
                st.subheader("Correlation Matrix")
                corr_matrix = calculate_correlation_matrix(results)
                st.dataframe(corr_matrix.style.format("{:.2f}").background_gradient(cmap='RdYlGn'))
            
            else:
                st.error("No results returned from backtest")
    else:
        st.info("Select coins and click 'Run Backtest' to start") 