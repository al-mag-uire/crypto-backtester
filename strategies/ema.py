from core.indicators import compute_rsi

def apply_ema_strategy(df, fast_period=12, slow_period=26, rsi_period=14, rsi_threshold=30):
    """
    Apply EMA crossover strategy with RSI filter
    Returns DataFrame with signals
    """
    # Make a copy to avoid modifying original data
    df = df.copy()
    
    # Calculate EMAs
    df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate RSI
    df['rsi'] = compute_rsi(df['close'], rsi_period)
    
    # Initialize signal column
    df['signal'] = 0
    
    # Generate signals
    # Buy when fast crosses above slow AND RSI is below threshold
    df.loc[(df['ema_fast'] > df['ema_slow']) & (df['rsi'] < rsi_threshold), 'signal'] = 1
    # Sell when fast crosses below slow
    df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = -1
    
    return df
