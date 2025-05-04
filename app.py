import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import requests
from crypto_backtester import (
    fetch_ohlcv, apply_strategy, backtest,
    COIN_ID, VS_CURRENCY, DAYS,
    EMA_FAST, EMA_SLOW,
    RSI_PERIOD, RSI_BUY_THRESHOLD,
    INITIAL_BALANCE, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    apply_mean_reversion_strategy, backtest_mean_reversion,
    apply_breakout_strategy, backtest_breakout,
    apply_macd_strategy, apply_bollinger_strategy
)

# Page config
st.set_page_config(layout="wide", page_title="Crypto Strategy Dashboard")
st.title("📈 Crypto Strategy Dashboard")

# === Strategy Selector ===
strategy = st.sidebar.selectbox("Choose Strategy", ["EMA Crossover", "RSI Mean Reversion", "Breakout", "MACD", "Bollinger Bands"])


# === Market Settings Shared ===
coin_options = {
    "Bitcoin (BTC)": "bitcoin",
    "Ethereum (ETH)": "ethereum",
    "Solana (SOL)": "solana",
    "Cardano (ADA)": "cardano",
    "Dogecoin (DOGE)": "dogecoin",
    "Fartcoin (FART)": "fartcoin"
}
selected_coin = st.sidebar.selectbox("Select Coin", list(coin_options.keys()))
coin = coin_options[selected_coin]
vs_currency = st.sidebar.text_input("Quote Currency", VS_CURRENCY)
days = st.sidebar.slider("Number of Days", 10, 90, int(DAYS))

# === EMA Crossover Strategy ===
if strategy == "EMA Crossover":
    with st.sidebar.form("ema_form"):
        st.header("EMA Strategy Parameters")
        fast = st.slider("Fast EMA", 5, 50, EMA_FAST)
        slow = st.slider("Slow EMA", 10, 100, EMA_SLOW)
        rsi_period = st.slider("RSI Period", 5, 30, RSI_PERIOD)
        rsi_threshold = st.slider("RSI Buy Threshold", 10, 50, RSI_BUY_THRESHOLD)
        sl_pct = st.slider("Stop Loss (%)", 1, 20, int(STOP_LOSS_PCT * 100)) / 100
        tp_pct = st.slider("Take Profit (%)", 1, 20, int(TAKE_PROFIT_PCT * 100)) / 100
        submitted = st.form_submit_button("Run Backtest")

    if submitted:
        with st.spinner("Validating Coin ID and fetching data..."):
            coin_check = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin}")
            if coin_check.status_code != 200:
                st.error(f"❌ Failed to fetch data for '{coin}'. Please check the CoinGecko ID.")
            else:
                try:
                    df = fetch_ohlcv(coin, vs_currency, days)
                    df = apply_strategy(df, fast, slow, rsi_period, rsi_threshold)
                    trades, pnl, final_val = backtest(df, INITIAL_BALANCE, sl_pct, tp_pct)
                    trades_df = pd.DataFrame(trades, columns=["timestamp", "action", "price"])

                    st.subheader("Backtest Summary")
                    st.metric("Final Value", f"${final_val:,.2f}")
                    st.metric("PnL", f"${pnl:,.2f}")
                    st.metric("Total Trades", len(trades))

                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
                    ax1.plot(df["timestamp"], df["close"], label="Price")
                    ax1.plot(df["timestamp"], df["ema_fast"], label=f"EMA {fast}")
                    ax1.plot(df["timestamp"], df["ema_slow"], label=f"EMA {slow}")

                    for i, row in trades_df.iterrows():
                        if "BUY" in row["action"]:
                            ax1.scatter(row["timestamp"], row["price"], marker="^", color="limegreen", label="Buy" if i == 0 else "", s=100, edgecolor="black")
                        elif "SELL" in row["action"]:
                            ax1.scatter(row["timestamp"], row["price"], marker="v", color="crimson", label="Sell" if i == 0 else "", s=100, edgecolor="black")
                    ax1.legend()
                    ax1.set_title(f"Trade Chart: {selected_coin}")

                    ax2.plot(df["timestamp"], df["rsi"], label="RSI", color="purple")
                    ax2.axhline(30, color="red", linestyle="--", label="RSI 30")
                    ax2.axhline(70, color="green", linestyle="--", label="RSI 70")
                    ax2.set_ylim(0, 100)
                    ax2.set_title("RSI")
                    ax2.legend()

                    st.pyplot(fig)
                    st.subheader("Trade Log")
                    st.dataframe(trades_df, use_container_width=True)

                except Exception as e:
                    st.error(f"❌ An error occurred while processing data: {e}")

# === RSI Mean Reversion Strategy ===
elif strategy == "RSI Mean Reversion":
    with st.sidebar.form("rsi_form"):
        st.header("Mean Reversion Parameters")
        rsi_period = st.slider("RSI Period", 5, 30, 14)
        rsi_buy = st.slider("RSI Buy Threshold", 10, 40, 25)
        rsi_sell = st.slider("RSI Sell Threshold", 60, 90, 70)
        sl_pct = st.slider("Stop Loss (%)", 1, 20, 5) / 100
        tp_pct = st.slider("Take Profit (%)", 1, 20, 10) / 100
        submitted = st.form_submit_button("Run Backtest")

    if submitted:
        with st.spinner("Validating Coin ID and fetching data..."):
            coin_check = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin}")
            if coin_check.status_code != 200:
                st.error(f"❌ Failed to fetch data for '{coin}'. Please check the CoinGecko ID.")
            else:
                try:
                    df = fetch_ohlcv(coin, vs_currency, days)
                    df = apply_mean_reversion_strategy(df, rsi_period, rsi_buy, rsi_sell)
                    trades, pnl, final_val = backtest_mean_reversion(df, INITIAL_BALANCE, sl_pct, tp_pct)
                    trades_df = pd.DataFrame(trades, columns=["timestamp", "action", "price"])

                    st.subheader("Backtest Summary")
                    st.metric("Final Value", f"${final_val:,.2f}")
                    st.metric("PnL", f"${pnl:,.2f}")
                    st.metric("Total Trades", len(trades))

                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
                    ax1.plot(df["timestamp"], df["close"], label="Price")

                    for i, row in trades_df.iterrows():
                        if "BUY" in row["action"]:
                            ax1.scatter(row["timestamp"], row["price"], marker="^", color="limegreen", label="Buy" if i == 0 else "", s=100, edgecolor="black")
                        elif "SELL" in row["action"]:
                            ax1.scatter(row["timestamp"], row["price"], marker="v", color="crimson", label="Sell" if i == 0 else "", s=100, edgecolor="black")
                    ax1.legend()
                    ax1.set_title(f"Trade Chart: {selected_coin}")

                    ax2.plot(df["timestamp"], df["rsi"], label="RSI", color="purple")
                    ax2.axhline(rsi_buy, color="red", linestyle="--", label=f"RSI Buy < {rsi_buy}")
                    ax2.axhline(rsi_sell, color="green", linestyle="--", label=f"RSI Sell > {rsi_sell}")
                    ax2.set_ylim(0, 100)
                    ax2.set_title("RSI")
                    ax2.legend()

                    st.pyplot(fig)
                    st.subheader("Trade Log")
                    st.dataframe(trades_df, use_container_width=True)

                except Exception as e:
                    st.error(f"❌ An error occurred while processing data: {e}")

# === Breakout Strategy ===
if strategy == "Breakout":
    with st.sidebar.form("breakout_form"):
        st.header("Breakout Strategy Parameters")
        window = st.slider("Lookback Window (Bars)", 5, 50, 20)
        volume_filter = st.checkbox("Use Volume Filter", value=False)
        sl_pct = st.slider("Stop Loss (%)", 1, 20, 5) / 100
        tp_pct = st.slider("Take Profit (%)", 1, 20, 10) / 100
        submitted = st.form_submit_button("Run Backtest")

    if submitted:
        with st.spinner("Fetching data and applying strategy..."):
            try:
                coin_check = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin}")
                if coin_check.status_code != 200:
                    st.error(f"❌ Failed to fetch data for '{coin}'. Please check the CoinGecko ID.")
                else:
                    df = fetch_ohlcv(coin, vs_currency, days)
                    df = apply_breakout_strategy(df, window, volume_filter)
                    trades, pnl, final_val = backtest_breakout(df, INITIAL_BALANCE, sl_pct, tp_pct)
                    trades_df = pd.DataFrame(trades, columns=["timestamp", "action", "price"])

                    st.subheader("Backtest Summary")
                    st.metric("Final Value", f"${final_val:,.2f}")
                    st.metric("PnL", f"${pnl:,.2f}")
                    st.metric("Total Trades", len(trades))

                    fig, ax = plt.subplots(figsize=(14, 6))
                    ax.plot(df['timestamp'], df['close'], label='Price')
                    ax.plot(df['timestamp'], df['rolling_high'], label=f'{window}-bar High', linestyle='--')

                    for i, row in trades_df.iterrows():
                        if 'BUY' in row['action']:
                            ax.scatter(row['timestamp'], row['price'], marker='^', color='limegreen', label='Buy' if i == 0 else '', s=100, edgecolor='black')
                        elif 'SELL' in row['action']:
                            ax.scatter(row['timestamp'], row['price'], marker='v', color='crimson', label='Sell' if i == 0 else '', s=100, edgecolor='black')

                    ax.set_title(f"Breakout Strategy: {selected_coin}")
                    ax.legend()
                    st.pyplot(fig)

                    st.subheader("Trade Log")
                    st.dataframe(trades_df, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred: {e}")

# === MACD Strategy ===
if strategy == "MACD":
    with st.sidebar.form("macd_form"):
        st.header("MACD Strategy Parameters")
        fast = st.slider("MACD Fast EMA", 5, 30, 12)
        slow = st.slider("MACD Slow EMA", 10, 50, 26)
        signal = st.slider("MACD Signal EMA", 5, 20, 9)
        sl_pct = st.slider("Stop Loss (%)", 1, 20, 5) / 100
        tp_pct = st.slider("Take Profit (%)", 1, 20, 10) / 100
        submitted = st.form_submit_button("Run Backtest")

    if submitted:
        df = fetch_ohlcv(coin, vs_currency, days)
        df = apply_macd_strategy(df, fast, slow, signal)
        trades, pnl, final_val = backtest(df, INITIAL_BALANCE, sl_pct, tp_pct)
        trades_df = pd.DataFrame(trades, columns=["timestamp", "action", "price"])

        st.subheader("Backtest Summary")
        st.metric("Final Value", f"${final_val:,.2f}")
        st.metric("PnL", f"${pnl:,.2f}")
        st.metric("Total Trades", len(trades))

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(df['timestamp'], df['close'], label='Price')
        for i, row in trades_df.iterrows():
            if 'BUY' in row['action']:
                ax.scatter(row['timestamp'], row['price'], marker='^', color='limegreen', label='Buy' if i == 0 else '', s=100, edgecolor='black')
            elif 'SELL' in row['action']:
                ax.scatter(row['timestamp'], row['price'], marker='v', color='crimson', label='Sell' if i == 0 else '', s=100, edgecolor='black')
        ax.set_title(f"MACD Strategy: {selected_coin}")
        ax.legend()
        st.pyplot(fig)
        st.subheader("Trade Log")
        st.dataframe(trades_df, use_container_width=True)



# === Bollinger Bands Strategy ===
elif strategy == "Bollinger Bands":
    with st.sidebar.form("bb_form"):
        st.header("Bollinger Bands Parameters")
        window = st.slider("Window Length", 10, 50, 20)
        num_std = st.slider("# of Std Dev", 1, 3, 2)
        sl_pct = st.slider("Stop Loss (%)", 1, 20, 5) / 100
        tp_pct = st.slider("Take Profit (%)", 1, 20, 10) / 100
        submitted = st.form_submit_button("Run Backtest")

    if submitted:
        df = fetch_ohlcv(coin, vs_currency, days)
        df = apply_bollinger_strategy(df, window, num_std)
        trades, pnl, final_val = backtest(df, INITIAL_BALANCE, sl_pct, tp_pct)
        trades_df = pd.DataFrame(trades, columns=["timestamp", "action", "price"])

        st.subheader("Backtest Summary")
        st.metric("Final Value", f"${final_val:,.2f}")
        st.metric("PnL", f"${pnl:,.2f}")
        st.metric("Total Trades", len(trades))

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(df['timestamp'], df['close'], label='Price')
        ax.plot(df['timestamp'], df['upper_band'], linestyle='--', label='Upper Band')
        ax.plot(df['timestamp'], df['lower_band'], linestyle='--', label='Lower Band')
        for i, row in trades_df.iterrows():
            if 'BUY' in row['action']:
                ax.scatter(row['timestamp'], row['price'], marker='^', color='limegreen', label='Buy' if i == 0 else '', s=100, edgecolor='black')
            elif 'SELL' in row['action']:
                ax.scatter(row['timestamp'], row['price'], marker='v', color='crimson', label='Sell' if i == 0 else '', s=100, edgecolor='black')
        ax.set_title(f"Bollinger Bands Strategy: {selected_coin}")
        ax.legend()
        st.pyplot(fig)
        st.subheader("Trade Log")
        st.dataframe(trades_df, use_container_width=True)
