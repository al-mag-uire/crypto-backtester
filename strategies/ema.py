import pandas as pd
import numpy as np
from typing import Dict, Any
import streamlit as st
import matplotlib.pyplot as plt
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_ema_strategy(df: pd.DataFrame, 
                      fast: int = 12, 
                      slow: int = 26, 
                      rsi_period: int = 14, 
                      rsi_oversold: int = 30,
                      rsi_overbought: int = 70) -> pd.DataFrame:
    """
    Apply EMA Crossover strategy with RSI filters
    
    Strategy Logic:
    Buy when:
    1. Fast EMA crosses above Slow EMA OR
    2. RSI is oversold and price is above fast EMA
    
    Sell when:
    1. Fast EMA crosses below Slow EMA OR
    2. RSI reaches overbought levels
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
        # 1. Fast EMA crosses above Slow EMA OR
        # 2. RSI is oversold and price is above fast EMA
        if ((df['ema_fast'].iloc[i] > df['ema_slow'].iloc[i] and 
             df['ema_fast'].iloc[i-1] <= df['ema_slow'].iloc[i-1]) or
            (df['rsi'].iloc[i] < rsi_oversold and 
             df['close'].iloc[i] > df['ema_fast'].iloc[i])):
            df.iloc[i, df.columns.get_loc('signal')] = 1
            
        # Sell conditions:
        # 1. Fast EMA crosses below Slow EMA OR
        # 2. RSI reaches overbought levels
        elif ((df['ema_fast'].iloc[i] < df['ema_slow'].iloc[i] and 
               df['ema_fast'].iloc[i-1] >= df['ema_slow'].iloc[i-1]) or
              df['rsi'].iloc[i] > rsi_overbought):
            df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Display metrics
    strategy_params = {
        "Fast EMA": fast,
        "Slow EMA": slow,
        "RSI Period": rsi_period,
        "RSI Oversold": rsi_oversold,
        "RSI Overbought": rsi_overbought
    }
    display_strategy_metrics(df, strategy_params)
    
    return df
