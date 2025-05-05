import pandas as pd
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_bollinger_strategy(df: pd.DataFrame, window: int = 20, num_std: int = 2) -> pd.DataFrame:
    """Apply Bollinger Bands strategy."""
    # Calculate Bollinger Bands
    df['middle_band'] = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    df['upper_band'] = df['middle_band'] + (std * num_std)
    df['lower_band'] = df['middle_band'] - (std * num_std)
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    for i in range(1, len(df)):
        # Buy when price crosses below lower band
        if df['close'].iloc[i] < df['lower_band'].iloc[i] and df['close'].iloc[i-1] >= df['lower_band'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('signal')] = 1
        # Sell when price crosses above upper band
        elif df['close'].iloc[i] > df['upper_band'].iloc[i] and df['close'].iloc[i-1] <= df['upper_band'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Display metrics and chart
    strategy_params = {
        "Window Length": window,
        "Standard Deviations": num_std
    }
    display_strategy_metrics(df, strategy_params)
    plot_strategy_indicators(df, "bollinger")
    
    return df