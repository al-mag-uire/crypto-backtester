import pandas as pd
import requests


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

def fetch_price(symbol="BTC-USD"):
    url = f"https://api.coinbase.com/v2/prices/{symbol}/spot"
    response = requests.get(url)
    if response.status_code == 200:
        return float(response.json()["data"]["amount"])
    else:
        raise Exception(f"Failed to fetch price for {symbol}: {response.text}")