import pandas as pd
import requests
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
import streamlit as st
from requests.exceptions import Timeout, RequestException
import time
from .mock_data import generate_mock_data


def fetch_ohlcv(coin: str, vs_currency: str, days: int, testing_mode: bool = True) -> pd.DataFrame:
    """
    Fetch OHLCV data from CoinGecko or generate mock data
    """
    if testing_mode:
        st.info("🧪 Using mock data for testing")
        return generate_mock_data(days)
    
    # Real data fetching with rate limit handling
    MAX_RETRIES = 3
    TIMEOUT = 10  # seconds
    
    for attempt in range(MAX_RETRIES):
        try:
            # Initialize CoinGecko API
            cg = CoinGeckoAPI()
            
            with st.spinner(f'Fetching {coin} data (attempt {attempt + 1}/{MAX_RETRIES})...'):
                # Set timeout for the request
                session = requests.Session()
                session.request = lambda *args, **kwargs: requests.request(*args, **{**kwargs, 'timeout': TIMEOUT})
                cg.session = session
                
                # Fetch OHLCV data
                ohlcv = cg.get_coin_ohlc_by_id(
                    id=coin.lower(),
                    vs_currency=vs_currency.lower(),
                    days=str(days)
                )
                
                if not ohlcv:
                    st.error(f"No data returned for {coin}")
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp')
                
                st.success(f"✅ Successfully fetched live {coin} data")
                return df
                
        except Exception as e:
            if "rate limit" in str(e).lower():
                st.error("⚠️ CoinGecko API rate limit reached. Try using Testing Mode.")
                return generate_mock_data(days)  # Fallback to mock data
            elif attempt < MAX_RETRIES - 1:
                st.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
            else:
                st.error(f"Failed to fetch data: {str(e)}")
                return pd.DataFrame()
    
    return pd.DataFrame()

def fetch_price(symbol="BTC-USD"):
    url = f"https://api.coinbase.com/v2/prices/{symbol}/spot"
    response = requests.get(url)
    if response.status_code == 200:
        return float(response.json()["data"]["amount"])
    else:
        raise Exception(f"Failed to fetch price for {symbol}: {response.text}")