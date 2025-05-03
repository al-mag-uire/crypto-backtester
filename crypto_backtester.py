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
INITIAL_BALANCE = 10000

# ============ FETCH DATA ============
def fetch_ohlcv(coin_id, vs_currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days
        # omit "interval" entirely
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = data.get("prices", [])
    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


# ============ STRATEGY LOGIC ============
def apply_strategy(df, fast=9, slow=21):
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['signal'] = 0
    df.loc[df['ema_fast'] > df['ema_slow'], 'signal'] = 1
    df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = -1
    df['position'] = df['signal'].shift(1)
    return df

# ============ BACKTEST ============
def backtest(df, initial_balance=10000):
    balance = initial_balance
    position = 0  # BTC amount
    trade_log = []

    for i in range(1, len(df)):
        signal = df.iloc[i]['position']
        price = df.iloc[i]['close']
        time = df.iloc[i]['timestamp']

        if signal == 1 and balance > 0:  # Buy
            position = balance / price
            balance = 0
            trade_log.append([time, 'BUY', price])

        elif signal == -1 and position > 0:  # Sell
            balance = position * price
            position = 0
            trade_log.append([time, 'SELL', price])

    # Final valuation
    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = balance

    pnl = final_value - initial_balance
    return trade_log, pnl, final_value

# ============ MAIN ============
if __name__ == "__main__":
    df = fetch_ohlcv(COIN_ID, VS_CURRENCY, DAYS)
    df = apply_strategy(df, EMA_FAST, EMA_SLOW)
    trades, pnl, final_val = backtest(df, INITIAL_BALANCE)

    # Save trade log
    trades_df = pd.DataFrame(trades, columns=['timestamp', 'action', 'price'])
    trades_df.to_csv("trades.csv", index=False)

    # Print results
    print(f"Final value: ${final_val:.2f}")
    print(f"PnL: ${pnl:.2f}")
    print(f"Total trades: {len(trades)}")

    # Plot
    plt.figure(figsize=(14, 6))
    plt.plot(df['timestamp'], df['close'], label='Price')
    plt.plot(df['timestamp'], df['ema_fast'], label=f'EMA {EMA_FAST}')
    plt.plot(df['timestamp'], df['ema_slow'], label=f'EMA {EMA_SLOW}')
    plt.legend()
    plt.title('EMA Crossover Strategy')
    plt.savefig('ema_crossover_strategy.png')
