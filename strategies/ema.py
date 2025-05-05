import pandas as pd
import numpy as np
from typing import Dict, Any
import streamlit as st
import matplotlib.pyplot as plt
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_ema_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26, rsi_period: int = 14, rsi_threshold: int = 30) -> pd.DataFrame:
    """
    Apply EMA Crossover strategy with RSI filter
    
    Args:
        df: DataFrame with OHLCV data
        fast: Fast EMA period
        slow: Slow EMA period
        rsi_period: RSI period
        rsi_threshold: RSI threshold for oversold condition
    """
    # Calculate EMAs
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    
    # Calculate RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    for i in range(1, len(df)):
        # Buy conditions:
        # 1. Fast EMA crosses above Slow EMA
        # 2. RSI is below threshold (oversold)
        if (df['ema_fast'].iloc[i] > df['ema_slow'].iloc[i] and 
            df['ema_fast'].iloc[i-1] <= df['ema_slow'].iloc[i-1] and 
            df['rsi'].iloc[i] < rsi_threshold):
            df.iloc[i, df.columns.get_loc('signal')] = 1
            
        # Sell conditions:
        # 1. Fast EMA crosses below Slow EMA
        elif (df['ema_fast'].iloc[i] < df['ema_slow'].iloc[i] and 
              df['ema_fast'].iloc[i-1] >= df['ema_slow'].iloc[i-1]):
            df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Display metrics and chart
    strategy_params = {
        "Fast EMA": fast,
        "Slow EMA": slow,
        "RSI Period": rsi_period,
        "RSI Threshold": rsi_threshold
    }
    display_strategy_metrics(df, strategy_params)
    plot_strategy_indicators(df, "ema")
    
    return df
