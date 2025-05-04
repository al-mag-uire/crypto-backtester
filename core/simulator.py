# core/simulator.py

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def simulate_over_time(df, strategy_func, broker, symbol, position_size=0.01, sl=None, tp=None, verbose=False):
    """
    Simulate strategy execution candle-by-candle on historical data.
    Trades are placed using the broker logic.

    Parameters:
        df: DataFrame with historical price data
        strategy_func: Function implementing the trading strategy
        broker: Broker object for trade execution
        symbol: Trading symbol
        position_size: Size of each position (default: 0.01)
        sl: Stop-loss level (optional)
        tp: Take-profit level (optional)
        verbose: Print trade notifications (default: False)
    Returns:
        trades: List of executed trades
        df: Modified DataFrame including equity curve
    """
    equity_curve = []
    trades = []
    
    # First apply strategy to get signals
    df = strategy_func(df.copy())
    
    if "signal" not in df.columns:
        raise ValueError("Strategy function must add a 'signal' column to the DataFrame")
        
    for i in range(1, len(df)):
        current_price = df['close'].iloc[i]
        current_time = df['timestamp'].iloc[i]
        current_signal = df['signal'].iloc[i]
        
        # Update stop loss and take profit relative to current price
        current_sl = current_price * (1 - sl) if sl else None
        current_tp = current_price * (1 + tp) if tp else None
        
        if verbose:
            print(f"{current_time}: Price=${current_price:.2f}, Signal={current_signal}")
            
        # Check for stop loss / take profit first
        if broker.check_stop_loss_take_profit(current_price, timestamp=current_time):
            if verbose:
                print(f"Stop loss or take profit triggered at ${current_price:.2f}")
                
        # Then check for new trade signals
        if current_signal == 1 and not broker.get_open_position():
            broker.buy(symbol, qty=position_size, price=current_price, 
                      sl=current_sl, tp=current_tp, timestamp=current_time)
            if verbose:
                print(f"BUY signal: Opened position at ${current_price:.2f}")
                
        elif current_signal == -1 and broker.get_open_position():
            broker.sell(symbol, price=current_price, timestamp=current_time)
            if verbose:
                print(f"SELL signal: Closed position at ${current_price:.2f}")
        
        # Update equity curve
        open_pos = broker.get_open_position()
        if open_pos:
            equity = broker.get_balance() + (current_price - open_pos['entry_price']) * open_pos['qty']
        else:
            equity = broker.get_balance()
        equity_curve.append(equity)
    
    df = df.iloc[1:].copy()  # Remove first row since we start at index 1
    df['equity'] = equity_curve
    
    return broker.get_trade_log(), df

def plot_price_and_equity(df, trades):
    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(df['timestamp'], df['close'], label='Price', color='blue')
    ax1.set_ylabel('Price', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    for trade in trades:
        ts = trade['timestamp']
        price = trade['price']
        if trade['side'] == 'buy':
            ax1.plot(ts, price, marker='^', color='green', markersize=10, label='Buy' if 'Buy' not in ax1.get_legend_handles_labels()[1] else "")
        else:
            ax1.plot(ts, price, marker='v', color='red', markersize=10, label='Sell' if 'Sell' not in ax1.get_legend_handles_labels()[1] else "")

    ax2 = ax1.twinx()
    ax2.plot(df['timestamp'], df['equity'], label='Equity', color='orange', linestyle='--')
    ax2.set_ylabel('Equity', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    fig.tight_layout()
    fig.legend(loc='upper left')
    st.subheader("📊 Price and Equity Curve")
    st.pyplot(fig)
    return fig
