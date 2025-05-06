import pandas as pd
import numpy as np
from utils.chart_utils import plot_strategy_indicators, display_strategy_metrics

def apply_breakout_strategy(df: pd.DataFrame, 
                          window: int = 20,
                          volatility_factor: float = 1.0,
                          volume_factor: float = 1.5) -> pd.DataFrame:
    """
    Apply Breakout strategy with volume confirmation
    
    Parameters:
        window: Lookback period for calculating rolling high/low
        volatility_factor: Multiplier for ATR to determine breakout threshold
        volume_factor: Required volume increase for confirmation
    """
    # Calculate rolling high/low
    df['rolling_high'] = df['high'].rolling(window=window).max()
    df['rolling_low'] = df['low'].rolling(window=window).min()
    
    # Calculate ATR for volatility threshold
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(window=window).mean()
    
    # Calculate volume threshold
    df['volume_ma'] = df['volume'].rolling(window=window).mean()
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    for i in range(1, len(df)):
        # Breakout conditions with volume confirmation
        if (df['close'].iloc[i] > df['rolling_high'].iloc[i-1] + df['atr'].iloc[i] * volatility_factor and
            df['volume'].iloc[i] > df['volume_ma'].iloc[i] * volume_factor):
            df.iloc[i, df.columns.get_loc('signal')] = 1
            
        elif (df['close'].iloc[i] < df['rolling_low'].iloc[i-1] - df['atr'].iloc[i] * volatility_factor and
              df['volume'].iloc[i] > df['volume_ma'].iloc[i] * volume_factor):
            df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Display metrics only
    strategy_params = {"Lookback Window": window, "Volatility Factor": volatility_factor, "Volume Factor": volume_factor}
    display_strategy_metrics(df, strategy_params)
    
    return df