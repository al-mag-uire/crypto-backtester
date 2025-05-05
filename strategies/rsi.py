import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_mean_reversion_strategy(
    df: pd.DataFrame, 
    rsi_period: int = 14,
    rsi_buy: int = 30,
    rsi_sell: int = 70
) -> pd.DataFrame:
    """Apply RSI Mean Reversion strategy with cleaner signal generation"""
    # Calculate RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals with state tracking to avoid signal clustering
    in_position = False
    for i in range(1, len(df)):
        if df['rsi'].iloc[i] < rsi_buy and not in_position:
            df.iloc[i, df.columns.get_loc('signal')] = 1
            in_position = True
        elif df['rsi'].iloc[i] > rsi_sell and in_position:
            df.iloc[i, df.columns.get_loc('signal')] = -1
            in_position = False
    
    # Display metrics and chart
    strategy_params = {
        "RSI Period": rsi_period,
        "RSI Buy Level": rsi_buy,
        "RSI Sell Level": rsi_sell
    }
    display_strategy_metrics(df, strategy_params)
    plot_strategy_indicators(df, "rsi")
    
    return df