import pandas as pd
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_breakout_strategy(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Apply Breakout strategy."""
    # Calculate rolling high and low
    df['rolling_high'] = df['high'].rolling(window=window).max()
    df['rolling_low'] = df['low'].rolling(window=window).min()
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    for i in range(1, len(df)):
        # Buy on breakout above previous high
        if df['close'].iloc[i] > df['rolling_high'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('signal')] = 1
        # Sell on breakdown below previous low
        elif df['close'].iloc[i] < df['rolling_low'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Display metrics and chart
    strategy_params = {"Lookback Window": window}
    display_strategy_metrics(df, strategy_params)
    plot_strategy_indicators(df, "breakout")
    
    return df