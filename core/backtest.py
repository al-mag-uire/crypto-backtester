# crypto_backtester.py

import pandas as pd
from typing import Dict, Any
import numpy as np

# ============ CONFIG ============
COIN_ID = 'bitcoin'  # CoinGecko ID
VS_CURRENCY = 'usd'
DAYS = '90'  # Max range: 90 for hourly
EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30
INITIAL_BALANCE = 10000
STOP_LOSS_PCT = 0.03  # 3%
TAKE_PROFIT_PCT = 0.05  # 5%


# ============ BACKTEST FUNCTIONS   ============
def backtest(df, initial_balance=10000, stop_loss_pct=0.05, take_profit_pct=0.1):
    """
    Backtest a strategy
    Returns: trades list, pnl, final_balance
    """
    trades = []
    balance = initial_balance
    position = None
    entry_price = 0
    
    for i in range(1, len(df)):
        current_price = df['close'].iloc[i]
        current_time = df['timestamp'].iloc[i]
        signal = df['signal'].iloc[i]
        
        # Check for stop loss/take profit if in position
        if position:
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Check stop loss
            if pnl_pct <= -stop_loss_pct:
                balance = balance * (1 + pnl_pct)
                trades.append([current_time, "SELL (SL)", current_price])
                position = None
                continue
                
            # Check take profit
            if pnl_pct >= take_profit_pct:
                balance = balance * (1 + pnl_pct)
                trades.append([current_time, "SELL (TP)", current_price])
                position = None
                continue
        
        # Regular signal processing
        if signal == 1 and not position:  # Buy signal
            position = "LONG"
            entry_price = current_price
            trades.append([current_time, "BUY", current_price])
            
        elif signal == -1 and position:  # Sell signal
            position = None
            pnl = (current_price - entry_price) / entry_price
            balance = balance * (1 + pnl)
            trades.append([current_time, "SELL", current_price])
    
    final_balance = balance
    pnl = final_balance - initial_balance
    
    return trades, pnl, final_balance


def backtest_mean_reversion(df, initial_balance=10000, stop_loss_pct=0.05, take_profit_pct=0.10):
    balance = initial_balance
    position = 0
    entry_price = 0
    trade_log = []

    for i in range(1, len(df)):
        signal = df.iloc[i]['position']
        price = df.iloc[i]['close']
        time = df.iloc[i]['timestamp']

        if signal == 1 and balance > 0:
            position = balance / price
            entry_price = price
            balance = 0
            trade_log.append([time, 'BUY', price])

        elif signal == -1 and position > 0:
            balance = position * price
            position = 0
            trade_log.append([time, 'SELL', price])

        elif position > 0:
            if price <= entry_price * (1 - stop_loss_pct):
                balance = position * price
                position = 0
                trade_log.append([time, 'SELL (SL)', price])
            elif price >= entry_price * (1 + take_profit_pct):
                balance = position * price
                position = 0
                trade_log.append([time, 'SELL (TP)', price])

    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = balance

    pnl = final_value - initial_balance
    return trade_log, pnl, final_value


def backtest_breakout(df, initial_balance=10000, stop_loss_pct=0.05, take_profit_pct=0.10):
    balance = initial_balance
    position = 0
    entry_price = 0
    trade_log = []

    for i in range(1, len(df)):
        signal = df.iloc[i]['position']
        price = df.iloc[i]['close']
        time = df.iloc[i]['timestamp']

        if signal == 1 and balance > 0:
            position = balance / price
            entry_price = price
            balance = 0
            trade_log.append([time, 'BUY', price])

        elif position > 0:
            if price <= entry_price * (1 - stop_loss_pct):
                balance = position * price
                position = 0
                trade_log.append([time, 'SELL (SL)', price])
            elif price >= entry_price * (1 + take_profit_pct):
                balance = position * price
                position = 0
                trade_log.append([time, 'SELL (TP)', price])

    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = balance

    pnl = final_value - initial_balance
    return trade_log, pnl, final_value


def run_backtest(
    df: pd.DataFrame,
    strategy_func: callable,
    strategy_params: Dict[str, Any],
    initial_capital: float = 10000,
    position_size: float = 0.5,
    stop_loss: float = 0.05,
    take_profit: float = 0.1
) -> Dict[str, pd.DataFrame]:
    """
    Run backtest for a given strategy.
    """
    # Initialize results DataFrame
    results = df.copy()
    
    # Reset index if it exists and ensure timestamp column is present
    if 'timestamp' not in results.columns and results.index.name == 'timestamp':
        results = results.reset_index()
    
    results['position'] = 0
    results['equity'] = initial_capital
    
    # Trading variables
    position = 0
    entry_price = 0
    capital = initial_capital
    trades = []
    
    # Get signals from DataFrame and store them
    signals = strategy_func(results)
    results['signal'] = signals['signal'] if isinstance(signals, pd.DataFrame) else signals
    
    # Iterate through data
    for i in range(1, len(results)):
        # Update equity with previous position's P&L
        if position != 0:
            price_change = (results.iloc[i]['close'] - results.iloc[i-1]['close']) / results.iloc[i-1]['close']
            capital = capital * (1 + position * price_change)
        
        results.iloc[i, results.columns.get_loc('equity')] = capital
        
        # Check for signals
        if results.iloc[i]['signal'] == 1 and position <= 0:  # Buy signal
            position = 1
            entry_price = results.iloc[i]['close']
            trades.append({
                'timestamp': results.iloc[i]['timestamp'],
                'type': 'buy',
                'price': entry_price,
                'capital': capital
            })
            
        elif results.iloc[i]['signal'] == -1 and position >= 0:  # Sell signal
            position = -1
            entry_price = results.iloc[i]['close']
            trades.append({
                'timestamp': results.iloc[i]['timestamp'],
                'type': 'sell',
                'price': entry_price,
                'capital': capital
            })
        
        results.iloc[i, results.columns.get_loc('position')] = position
    
    # Calculate drawdown
    results['peak'] = results['equity'].cummax()
    results['drawdown'] = (results['equity'] - results['peak']) / results['peak'] * 100
    
    # Create trades DataFrame
    trades_df = pd.DataFrame(trades)
    
    return {
        'results': results,
        'trades': trades_df if not trades_df.empty else pd.DataFrame(columns=['timestamp', 'type', 'price', 'capital'])
    }

