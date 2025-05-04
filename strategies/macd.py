def apply_macd_strategy(df, fast=12, slow=26, signal=9):
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    df['signal'] = 0
    df.loc[df['macd'] > df['macd_signal'], 'signal'] = 1
    df.loc[df['macd'] < df['macd_signal'], 'signal'] = -1
    df['position'] = df['signal'].shift(1)
    return df
