import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    # Calculate price changes
    delta = prices.diff()
    
    # Separate gains and losses
    gains = delta.copy()
    losses = delta.copy()
    gains[gains < 0] = 0
    losses[losses > 0] = 0
    losses = abs(losses)
    
    # Calculate average gains and losses
    avg_gains = gains.rolling(window=period).mean()
    avg_losses = losses.rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def apply_mean_reversion_strategy(
    df: pd.DataFrame, 
    rsi_period: int = 14,
    rsi_buy: int = 30,
    rsi_sell: int = 70
) -> pd.DataFrame:
    """Apply RSI mean reversion strategy"""
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'], period=rsi_period)
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    df.loc[df['rsi'] < rsi_buy, 'signal'] = 1  # Buy signal
    df.loc[df['rsi'] > rsi_sell, 'signal'] = -1  # Sell signal
    
    # Display metrics only
    strategy_params = {
        "RSI Period": rsi_period,
        "RSI Buy Level": rsi_buy,
        "RSI Sell Level": rsi_sell
    }
    display_strategy_metrics(df, strategy_params)
    
    return df