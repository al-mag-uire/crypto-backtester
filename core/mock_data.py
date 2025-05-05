import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_data(days: int = 30) -> pd.DataFrame:
    """
    Generate mock OHLCV data for testing
    
    Args:
        days: Number of days of data to generate
    """
    # Generate timestamps
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    timestamps = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # Generate mock price data
    np.random.seed(42)  # For reproducibility
    price = 30000  # Starting price for Bitcoin
    prices = []
    
    for _ in range(len(timestamps)):
        # Random walk with drift
        change = np.random.normal(0, 100)  # Mean 0, std 100
        price += change
        prices.append(price)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'close': prices
    })
    
    # Generate OHLC data
    df['open'] = df['close'].shift(1)
    df['high'] = df['close'] * (1 + abs(np.random.normal(0, 0.02, len(df))))
    df['low'] = df['close'] * (1 - abs(np.random.normal(0, 0.02, len(df))))
    
    # Fill first row's open price
    df.loc[0, 'open'] = df.loc[0, 'close'] * 0.99
    
    return df 