import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict

def show_performance_table(results: pd.DataFrame) -> None:
    """
    Display performance metrics table with strategy vs buy & hold comparison
    """
    # Calculate strategy metrics
    initial_balance = results['equity'].iloc[0]
    final_balance = results['equity'].iloc[-1]
    strategy_pnl = final_balance - initial_balance
    strategy_return = (final_balance / initial_balance - 1) * 100
    max_drawdown = results['drawdown'].min()
    
    # Calculate buy & hold metrics
    initial_price = results['close'].iloc[0]
    final_price = results['close'].iloc[-1]
    bh_return = (final_price / initial_price - 1) * 100
    bh_final = initial_balance * (1 + bh_return/100)
    bh_pnl = bh_final - initial_balance
    
    # Create metrics table
    metrics = {
        'Metric': ['Initial Balance', 'Final Balance', 'Total PnL', 'Return (%)', 'Max Drawdown (%)'],
        'Strategy': [
            f"${initial_balance:,.2f}",
            f"${final_balance:,.2f}",
            f"${strategy_pnl:,.2f}",
            f"{strategy_return:.2f}%",
            f"{max_drawdown:.2f}%"
        ],
        'Buy & Hold': [
            f"${initial_balance:,.2f}",
            f"${bh_final:,.2f}",
            f"${bh_pnl:,.2f}",
            f"{bh_return:.2f}%",
            "N/A"
        ]
    }
    
    # Display metrics
    st.table(pd.DataFrame(metrics))

def show_equity_curve(results: pd.DataFrame) -> None:
    """
    Display equity curve chart with buy & hold comparison
    """
    # Calculate buy & hold equity curve
    initial_balance = results['equity'].iloc[0]
    bh_returns = results['close'] / results['close'].iloc[0] - 1
    bh_equity = initial_balance * (1 + bh_returns)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot strategy equity
    ax.plot(results['timestamp'], results['equity'], 
            label='Strategy', color='blue', linewidth=2)
    
    # Plot buy & hold equity
    ax.plot(results['timestamp'], bh_equity, 
            label='Buy & Hold', color='gray', linestyle='--', alpha=0.8)
    
    ax.set_title('Strategy vs Buy & Hold Performance')
    ax.set_xlabel('Date')
    ax.set_ylabel('Account Value ($)')
    ax.grid(True)
    ax.legend()
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    st.pyplot(fig)
