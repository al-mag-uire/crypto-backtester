def apply_bollinger_strategy(df, window=20, num_std=2):
    df['sma'] = df['close'].rolling(window=window).mean()
    df['std'] = df['close'].rolling(window=window).std()
    df['upper_band'] = df['sma'] + (num_std * df['std'])
    df['lower_band'] = df['sma'] - (num_std * df['std'])
    df['signal'] = 0
    df.loc[df['close'] < df['lower_band'], 'signal'] = 1  # Buy
    df.loc[df['close'] > df['upper_band'], 'signal'] = -1  # Sell
    df['position'] = df['signal'].shift(1)
    return df