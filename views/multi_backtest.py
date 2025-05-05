import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
    elif strategy == "Breakout":
        params.update({
            "window": st.sidebar.slider("Lookback Window", 5, 50, 20)
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

def show_multi_backtest():
    """Display the multi-coin backtest page."""
    st.header("📊 Multi-Coin Backtest")
    
    # Strategy selection
    strategy_options = ["EMA", "RSI", "Breakout", "MACD", "Bollinger"]
    strategy = st.selectbox("Select Strategy", strategy_options)
    
    # Coin selection
    available_coins = {
        "Bitcoin (BTC)": "bitcoin",
        "Ethereum (ETH)": "ethereum",
        "Solana (SOL)": "solana",
        "Cardano (ADA)": "cardano",
        "Polkadot (DOT)": "polkadot",
        "Chainlink (LINK)": "chainlink",
        "Avalanche (AVAX)": "avalanche-2",
        "Polygon (MATIC)": "matic-network"
    }
    
    selected_coins = st.multiselect(
        "Select Coins",
        options=list(available_coins.keys()),
        default=list(available_coins.keys())[:4]
    )
    
    if not selected_coins:
        st.warning("Please select at least one coin.")
        return
        
    coins = [available_coins[coin] for coin in selected_coins]
    
    # Get parameters
    backtest_params, submitted = get_multi_backtest_params()
    strategy_params = get_strategy_params(strategy)
    
    if submitted:
        with st.spinner("Running multi-coin backtest..."):
            try:
                # Map strategy functions
                strategy_funcs = {
                    "EMA": apply_ema_strategy,
                    "RSI": apply_mean_reversion_strategy,
                    "Breakout": apply_breakout_strategy,
                    "MACD": apply_macd_strategy,
                    "Bollinger Bands": apply_bollinger_strategy
                }
                
                # Run backtest
                results, coin_metrics = run_multi_backtest(
                    coins=coins,
                    strategy_func=strategy_funcs[strategy],
                    strategy_params=strategy_params,
                    initial_balance=backtest_params["initial_balance"],
                    position_size=backtest_params["position_size"],
                    stop_loss=backtest_params["stop_loss"],
                    take_profit=backtest_params["take_profit"],
                    days=backtest_params["days"],
                    rebalance_days=backtest_params["rebalance_days"]
                )
                
                # Display overall results
                final_equity = results['total_equity'].iloc[-1]
                total_return = (final_equity - backtest_params["initial_balance"]) / backtest_params["initial_balance"] * 100
                max_drawdown = (results['total_equity'] / results['total_equity'].cummax() - 1).min() * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Final Portfolio Value", f"${final_equity:,.2f}")
                with col2:
                    st.metric("Total Return", f"{total_return:.1f}%")
                with col3:
                    st.metric("Max Drawdown", f"{max_drawdown:.1f}%")
                
                # Plot portfolio performance
                st.subheader("Portfolio Performance")
                plot_portfolio_performance(results)
                
                # Display individual coin metrics
                st.subheader("Individual Coin Performance")
                metrics_df = pd.DataFrame(coin_metrics).T
                metrics_df.columns = ["Total Trades", "Win Rate", "Profit/Loss", "Return %"]
                st.dataframe(metrics_df, use_container_width=True)
                
                # Display trade history
                st.subheader("Trade History")
                if 'trades' in results:
                    trades_df = results['trades'].copy()
                    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
                    st.dataframe(trades_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.write("Error details:", e.__class__.__name__) 