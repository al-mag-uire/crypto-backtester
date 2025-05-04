from core.indicators import compute_rsi

def apply_ema_strategy(df, fast=9, slow=21, rsi_period=14, rsi_threshold=30):
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['rsi'] = compute_rsi(df['close'], rsi_period)

    df['signal'] = 0
    df.loc[(df['ema_fast'] > df['ema_slow']) & (df['rsi'] < rsi_threshold), 'signal'] = 1
    df.loc[(df['ema_fast'] < df['ema_slow']), 'signal'] = -1
    df['position'] = df['signal'].shift(1)
    return df
