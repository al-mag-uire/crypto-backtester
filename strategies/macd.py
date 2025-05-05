import pandas as pd
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_macd_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Apply MACD strategy."""
    # Calculate indicators
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    df['hist'] = df['macd'] - df['macd_signal']
    df['signal'] = 0
    
    # Generate signals on crossovers
    for i in range(1, len(df)):
        if df['macd'].iloc[i] > df['macd_signal'].iloc[i] and df['macd'].iloc[i-1] <= df['macd_signal'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('signal')] = 1
        elif df['macd'].iloc[i] < df['macd_signal'].iloc[i] and df['macd'].iloc[i-1] >= df['macd_signal'].iloc[i-1]:
            df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Display metrics and chart
    strategy_params = {"Fast Period": fast, "Slow Period": slow, "Signal Period": signal}
    display_strategy_metrics(df, strategy_params)
    plot_strategy_indicators(df, "macd")
    
    return df
