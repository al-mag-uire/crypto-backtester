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
from typing import List, Dict, Any

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

def run_multi_backtest(
    coins: List[str],
    strategy: str,
    days: int,
    initial_balance: float,
    position_size: float,
    stop_loss: float,
    take_profit: float,
    rebalance_days: int,
    strategy_params: Dict[str, Any],
    testing_mode: bool = True
) -> Dict[str, Any]:
    """
    Run backtest across multiple coins with portfolio-level tracking
    """
    results = {}
    portfolio_equity = pd.Series(dtype=float)
    allocation_per_coin = initial_balance * position_size
    
    # Strategy function mapping
    strategy_funcs = {
        'ema': apply_ema_strategy,
        'rsi': apply_mean_reversion_strategy,
        'macd': apply_macd_strategy,
        'bollinger': apply_bollinger_strategy,
        'breakout': apply_breakout_strategy
    }
    
    if strategy not in strategy_funcs:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    strategy_func = strategy_funcs[strategy]
    
    # First fetch all data and align dates
    coin_data = {}
    common_dates = None
    
    for coin in coins:
        try:
            df = fetch_with_cache(coin, "usd", days)
            if not df.empty:
                coin_data[coin] = df
                if common_dates is None:
                    common_dates = set(df.index)
                else:
                    common_dates = common_dates.intersection(set(df.index))
        except Exception as e:
            print(f"Error fetching {coin}: {str(e)}")
            continue
    
    if not coin_data:
        return results
    
    # Align all dataframes to common dates
    common_dates = sorted(list(common_dates))
    for coin in coin_data:
        coin_data[coin] = coin_data[coin].loc[common_dates]
    
    # Run backtest for each coin
    for coin, df in coin_data.items():
        try:
            # Apply strategy
            df = strategy_func(df.copy(), **strategy_params)
            
            # Run backtest
            trades, pnl, final_balance = backtest(
                df,
                initial_balance=allocation_per_coin,
                stop_loss_pct=stop_loss,
                take_profit_pct=take_profit
            )
            
            # Calculate metrics
            win_rate, sharpe_ratio = calculate_metrics(trades, df, allocation_per_coin, final_balance)
            
            results[coin] = {
                'trades': trades,
                'pnl': pnl,
                'final_balance': final_balance,
                'return_pct': (final_balance - allocation_per_coin) / allocation_per_coin * 100,
                'win_rate': win_rate,
                'sharpe_ratio': sharpe_ratio,
                'equity_curve': df['equity']
            }
            
            # Add to portfolio equity
            if portfolio_equity.empty:
                portfolio_equity = df['equity']
            else:
                portfolio_equity = portfolio_equity.add(df['equity'])
            
        except Exception as e:
            print(f"Error processing {coin}: {str(e)}")
            continue
    
    # Add portfolio-level metrics
    if results:
        portfolio_return = (portfolio_equity.iloc[-1] - initial_balance) / initial_balance * 100
        portfolio_drawdown = (portfolio_equity / portfolio_equity.cummax() - 1).min() * 100
        
        results['portfolio'] = {
            'equity_curve': portfolio_equity,
            'final_balance': portfolio_equity.iloc[-1],
            'return_pct': portfolio_return,
            'max_drawdown_pct': portfolio_drawdown
        }
    
    return results

# Example usage:
if __name__ == "__main__":
    coins = ["bitcoin", "ethereum", "solana", "cardano"]
    df_results = run_multi_backtest(coins, "ema", 30, 10000, 0.2, 0.05, 0.1, 7, {}, True)
    print(df_results)
