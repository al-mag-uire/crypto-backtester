import pandas as pd
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_macd_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Apply MACD strategy with crossover signals"""
    # Calculate MACD
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    df['hist'] = df['macd'] - df['macd_signal']
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals based on MACD crossing Signal line
    for i in range(1, len(df)):
        # Buy when MACD crosses above Signal line
        if (df['macd'].iloc[i] > df['macd_signal'].iloc[i] and 
            df['macd'].iloc[i-1] <= df['macd_signal'].iloc[i-1]):
            df.iloc[i, df.columns.get_loc('signal')] = 1
            
        # Sell when MACD crosses below Signal line
        elif (df['macd'].iloc[i] < df['macd_signal'].iloc[i] and 
              df['macd'].iloc[i-1] >= df['macd_signal'].iloc[i-1]):
            df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Display metrics only
    strategy_params = {
        "Fast Period": fast,
        "Slow Period": slow,
        "Signal Period": signal
    }
    display_strategy_metrics(df, strategy_params)
    
    return df
