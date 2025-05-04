# crypto_backtester.py

import pandas as pd

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
def backtest(df, initial_balance=10000, stop_loss_pct=0.03, take_profit_pct=0.05):
    balance = initial_balance
    position = 0
    entry_price = 0
    trade_log = []

    for i in range(1, len(df)):
        signal = df.iloc[i]['position']
        price = df.iloc[i]['close']
        time = df.iloc[i]['timestamp']

        if signal == 1 and balance > 0:  # Buy
            position = balance / price
            entry_price = price
            balance = 0
            trade_log.append([time, 'BUY', price])

        elif position > 0:
            # Check for take-profit or stop-loss
            if price >= entry_price * (1 + take_profit_pct):
                balance = position * price
                position = 0
                trade_log.append([time, 'SELL (TP)', price])

            elif price <= entry_price * (1 - stop_loss_pct):
                balance = position * price
                position = 0
                trade_log.append([time, 'SELL (SL)', price])

            elif signal == -1:
                balance = position * price
                position = 0
                trade_log.append([time, 'SELL', price])

    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = balance

    pnl = final_value - initial_balance
    return trade_log, pnl, final_value


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

