from core.indicators import compute_rsi

def apply_mean_reversion_strategy(df, rsi_period=14, rsi_buy=25, rsi_sell=70):
    df['rsi'] = compute_rsi(df['close'], rsi_period)
    df['signal'] = 0
    df.loc[df['rsi'] < rsi_buy, 'signal'] = 1   # Buy signal
    df.loc[df['rsi'] > rsi_sell, 'signal'] = -1  # Sell signal
    df['position'] = df['signal'].shift(1)
    return df