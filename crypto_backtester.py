# crypto_backtester.py

import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

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

# ============ FETCH DATA ============
def fetch_ohlcv(coin_id, vs_currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = data.get("prices", [])
    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# ============ STRATEGY LOGIC ============
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def apply_strategy(df, fast=9, slow=21, rsi_period=14, rsi_threshold=30):
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['rsi'] = compute_rsi(df['close'], rsi_period)

    df['signal'] = 0
    buy_condition = (df['ema_fast'] > df['ema_slow']) & (df['rsi'] < rsi_threshold)
    sell_condition = (df['ema_fast'] < df['ema_slow'])

    df.loc[buy_condition, 'signal'] = 1
    df.loc[sell_condition, 'signal'] = -1
    df['position'] = df['signal'].shift(1)
    return df

# ============ BACKTEST ============
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

# ============ MEAN REVERSION STRATEGY ============
def apply_mean_reversion_strategy(df, rsi_period=14, rsi_buy=25, rsi_sell=70):
    df['rsi'] = compute_rsi(df['close'], rsi_period)
    df['signal'] = 0
    df.loc[df['rsi'] < rsi_buy, 'signal'] = 1   # Buy signal
    df.loc[df['rsi'] > rsi_sell, 'signal'] = -1  # Sell signal
    df['position'] = df['signal'].shift(1)
    return df

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

# ============ BREAKOUT STRATEGY ============
def apply_breakout_strategy(df, window=20, volume_filter=False):
    df['rolling_high'] = df['close'].shift(1).rolling(window=window).max()
    df['signal'] = 0
    if volume_filter and 'volume' in df.columns:
        volume_avg = df['volume'].rolling(window=window).mean()
        df.loc[(df['close'] > df['rolling_high']) & (df['volume'] > volume_avg), 'signal'] = 1
    else:
        df.loc[df['close'] > df['rolling_high'], 'signal'] = 1
    df['position'] = df['signal'].shift(1)
    return df

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

# ============ MACD STRATEGY ============
def apply_macd_strategy(df, fast=12, slow=26, signal=9):
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    df['signal'] = 0
    df.loc[df['macd'] > df['macd_signal'], 'signal'] = 1
    df.loc[df['macd'] < df['macd_signal'], 'signal'] = -1
    df['position'] = df['signal'].shift(1)
    return df

# ============ BOLLINGER STRATEGY ============
def apply_bollinger_strategy(df, window=20, num_std=2):
    df['sma'] = df['close'].rolling(window=window).mean()
    df['std'] = df['close'].rolling(window=window).std()
    df['upper_band'] = df['sma'] + (num_std * df['std'])
    df['lower_band'] = df['sma'] - (num_std * df['std'])
    df['signal'] = 0
    df.loc[df['close'] < df['lower_band'], 'signal'] = 1  # Buy
    df.loc[df['close'] > df['upper_band'], 'signal'] = -1  # Sell
    df['position'] = df['signal'].shift(1)
    return df
