import pandas as pd
from core.backtest import backtest, backtest_mean_reversion, backtest_breakout
from strategies.ema import apply_ema_strategy
from strategies.rsi import apply_mean_reversion_strategy
from strategies.breakout import apply_breakout_strategy
from strategies.macd import apply_macd_strategy
from strategies.bollinger import apply_bollinger_strategy
from core.fetch import fetch_ohlcv
from core.paper_broker import PaperBroker
from core.simulator import simulate_over_time
import numpy as np
import os
import hashlib
import json

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_key(coin, vs_currency, days):
    # Add timestamp to ensure we don't use stale data
    timestamp = pd.Timestamp.now().floor('D').timestamp()
    key_str = f"{coin}_{vs_currency}_{days}_{timestamp}"
    return os.path.join(CACHE_DIR, hashlib.md5(key_str.encode()).hexdigest() + ".json")

def fetch_with_cache(coin, vs_currency, days):
    cache_file = get_cache_key(coin, vs_currency, days)
    
    if os.path.exists(cache_file):
        try:
            # Check if cache is from today
            file_age = pd.Timestamp.now().timestamp() - os.path.getmtime(cache_file)
            if file_age < 24 * 3600:  # Cache is less than 24 hours old
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    df = pd.DataFrame(cached_data)
                    # Ensure datetime index is properly restored
                    df.index = pd.to_datetime(df.index)
                    return df
        except Exception as e:
            print(f"Cache read failed for {coin}: {e}")
            # If cache read fails, delete corrupt cache file
            if os.path.exists(cache_file):
                os.remove(cache_file)

    # Fetch new data
    df = fetch_ohlcv(coin, vs_currency, days)
    
    if df.empty:
        print(f"No data returned from API for {coin}")
        return df
        
    if not df.empty:
        try:
            # Convert timestamps to ISO format strings before serializing
            df_to_save = df.copy()
            df_to_save.index = df_to_save.index.strftime('%Y-%m-%d %H:%M:%S')
            
            # Convert to JSON-serializable format
            json_data = df_to_save.reset_index().to_dict(orient='records')
            with open(cache_file, 'w') as f:
                json.dump(json_data, f)
        except Exception as e:
            print(f"Cache write failed for {coin}: {e}")
            # If cache write fails, delete corrupt cache file
            if os.path.exists(cache_file):
                os.remove(cache_file)
    
    return df

def calculate_metrics(trades, df, initial_balance, final_balance):
    pnl = final_balance - initial_balance

    sell_trades = [t for t in trades if t['side'] == 'sell']
    buy_prices = [t['price'] for t in trades if t['side'] == 'buy']
    sell_prices = [t['price'] for t in trades if t['side'] == 'sell']

    # Calculate win rate
    wins = [1 for b, s in zip(buy_prices, sell_prices) if s > b]
    total = len(sell_prices)
    win_rate = (sum(wins) / total * 100) if total > 0 else 0.0

    # Calculate daily returns for Sharpe ratio
    df = df.copy()
    df['returns'] = df['equity'].pct_change().fillna(0)
    sharpe_ratio = (df['returns'].mean() / df['returns'].std()) * np.sqrt(365) if df['returns'].std() > 0 else 0.0

    return pnl, win_rate, sharpe_ratio

def run_multi_backtest(coins, strategy_func, strategy_name, vs_currency="usd", days=30):
    results = []
    for coin in coins:
        try:
            df = fetch_with_cache(coin, vs_currency, days)
            if df.empty:
                print(f"No data for {coin}")
                continue

            broker = PaperBroker(initial_balance=10000)
            trades, df = simulate_over_time(df, strategy_func, broker, coin)
            final_val = broker.get_balance()

            pnl, win_rate, sharpe = calculate_metrics(trades, df, 10000, final_val)

            results.append({
                "Coin": coin,
                "Strategy": strategy_name,
                "Total Trades": len(trades),
                "PnL": round(pnl, 2),
                "Final Balance": round(final_val, 2),
                "Win Rate (%)": round(win_rate, 2),
                "Sharpe Ratio": round(sharpe, 2)
            })
        except Exception as e:
            print(f"Error processing {coin}: {e}")

    return pd.DataFrame(results)

# Example usage:
if __name__ == "__main__":
    coins = ["bitcoin", "ethereum", "solana", "cardano"]
    df_results = run_multi_backtest(coins, apply_ema_strategy, "EMA")
    print(df_results)
