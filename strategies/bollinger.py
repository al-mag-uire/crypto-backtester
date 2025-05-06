import pandas as pd
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_bollinger_strategy(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Apply Bollinger Bands strategy"""
    # Calculate Bollinger Bands
    df['middle_band'] = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    df['upper_band'] = df['middle_band'] + (std * num_std)
    df['lower_band'] = df['middle_band'] - (std * num_std)
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    df.loc[df['close'] < df['lower_band'], 'signal'] = 1  # Buy signal
    df.loc[df['close'] > df['upper_band'], 'signal'] = -1  # Sell signal
    
    # Display metrics only
    strategy_params = {
        "Window": window,
        "Standard Deviations": num_std
    }
    display_strategy_metrics(df, strategy_params)
    
    return df