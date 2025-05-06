import pandas as pd
import requests
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
import streamlit as st
from requests.exceptions import Timeout, RequestException
import time
from .mock_data import generate_mock_data
import os
from pathlib import Path
import ccxt
import json
import hashlib

# Use existing cache directory
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Create global fetcher instance
_fetcher = None

def get_fetcher():
    global _fetcher
    if _fetcher is None:
        _fetcher = DataFetcher()
    return _fetcher

class DataFetcher:
    def __init__(self, exchange: str = 'coinbase'):
        self.exchange = getattr(ccxt, exchange)()
        self.exchange.enableRateLimit = True
        
        # Load markets to get actual symbols
        self.markets = self.exchange.load_markets()
        
        # Debug info about available pairs
        btc_pairs = [s for s in self.markets.keys() if 'BTC' in s]
        eth_pairs = [s for s in self.markets.keys() if 'ETH' in s]
        print(f"Available pairs on {exchange}:")
        print(f"BTC pairs: {btc_pairs}")
        print(f"ETH pairs: {eth_pairs}")
        
        # Coinbase mappings
        self.exchange_mappings = {
            'bitcoin': 'BTC',
            'btc': 'BTC',
            'ethereum': 'ETH',
            'eth': 'ETH',
            'solana': 'SOL',
            'sol': 'SOL',
            'cardano': 'ADA',
            'ada': 'ADA',
            'usd': 'USDC',  # Changed from USD to USDC
            'usdt': 'USDT'
        }
    
    def _get_cache_key(self, symbol: str, timeframe: str, days: int):
        # Use your existing cache key function
        timestamp = pd.Timestamp.now().floor('D').timestamp()
        key_str = f"{symbol}_{timeframe}_{days}_{timestamp}"
        return os.path.join(CACHE_DIR, hashlib.md5(key_str.encode()).hexdigest() + ".json")

    def _format_symbol(self, coin: str, vs_currency: str) -> str:
        """Format symbol according to Coinbase requirements"""
        coin = coin.lower()
        vs_currency = vs_currency.lower()
        
        # Map to exchange codes
        coin_code = self.exchange_mappings.get(coin, coin.upper())
        vs_code = self.exchange_mappings.get(vs_currency, vs_currency.upper())
        
        # Try different symbol formats
        possible_symbols = [
            f"{coin_code}/{vs_code}",        # BTC/USDC
            f"{coin_code}-{vs_code}",        # BTC-USDC
            f"{coin_code}/{vs_currency}",    # BTC/USD (fallback)
        ]
        
        for symbol in possible_symbols:
            if symbol in self.markets:
                st.success(f"Found valid symbol: {symbol}")
                return symbol
        
        # If no valid symbol found, show available options
        available = [s for s in self.markets.keys() 
                    if coin_code in s.split('/')[0]]  # Only show pairs for the selected coin
        
        error_msg = (
            f"No valid symbol found for {coin}/{vs_currency}.\n"
            f"Tried formats: {possible_symbols}\n"
            f"Available pairs: {available[:5]}"
        )
        st.error(error_msg)
        raise ValueError(error_msg)

    def fetch_ohlcv(self, coin: str, vs_currency: str, days: int, testing_mode: bool = True) -> pd.DataFrame:
        """Fetch OHLCV data using existing interface"""
        if testing_mode:
            st.info("🧪 Using mock data for testing")
            return generate_mock_data(days)
            
        cache_file = self._get_cache_key(coin, vs_currency, days)
        
        # Try to get from cache first
        if os.path.exists(cache_file):
            try:
                file_age = pd.Timestamp.now().timestamp() - os.path.getmtime(cache_file)
                if file_age < 24 * 3600:  # Cache is less than 24 hours old
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        df = pd.DataFrame(cached_data)
                        # Properly restore the datetime index
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                        return df
            except Exception as e:
                print(f"Cache read failed for {coin}: {e}")
                if os.path.exists(cache_file):
                    os.remove(cache_file)

        # Fetch new data if cache miss
        try:
            symbol = self._format_symbol(coin, vs_currency)
            since = self.exchange.parse8601(f"{days} days ago UTC")
            
            st.info(f"Fetching {symbol} data from {self.exchange.name}...")
            
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe='1h',
                since=since
            )
            
            if not ohlcv:
                st.error(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Save to cache
            df_to_save = df.copy()
            # Save timestamp as string in cache
            df_to_save = df_to_save.reset_index()
            df_to_save['timestamp'] = df_to_save['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            json_data = df_to_save.to_dict(orient='records')
            with open(cache_file, 'w') as f:
                json.dump(json_data, f)
            
            st.success(f"✅ Successfully fetched {symbol} data from {self.exchange.name}")
            return df
            
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                st.error(f"Rate limit reached on {self.exchange.name}. Try again in a few minutes.")
            else:
                st.error(f"Failed to fetch data: {error_msg}")
            return pd.DataFrame()

def fetch_price(symbol="BTC-USD"):
    url = f"https://api.coinbase.com/v2/prices/{symbol}/spot"
    response = requests.get(url)
    if response.status_code == 200:
        return float(response.json()["data"]["amount"])
    else:
        raise Exception(f"Failed to fetch price for {symbol}: {response.text}")

# Maintain the original function interface
def fetch_ohlcv(coin: str, vs_currency: str, days: int, testing_mode: bool = True) -> pd.DataFrame:
    """
    Fetch OHLCV data using existing interface
    """
    fetcher = get_fetcher()
    return fetcher.fetch_ohlcv(coin, vs_currency, days, testing_mode)