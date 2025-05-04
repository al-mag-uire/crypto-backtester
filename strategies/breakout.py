def apply_breakout_strategy(df, window=20, volume_filter=False):
    df['rolling_high'] = df['close'].shift(1).rolling(window=window).max()
    df['signal'] = 0
    if volume_filter and 'volume' in df.columns:
        volume_avg = df['volume'].rolling(window=window).mean()
        df.loc[(df['close'] > df['rolling_high']) & (df['volume'] > volume_avg), 'signal'] = 1
    else:
        df.loc[df['close'] > df['rolling_high'], 'signal'] = 1
    df['position'] = df['signal'].shift(1)
    return df