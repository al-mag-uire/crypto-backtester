import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import requests
import pathlib
import os

# Core utils
from core.fetch import fetch_ohlcv, fetch_price
from core.indicators import compute_rsi
from core.backtest import (
    COIN_ID, VS_CURRENCY, DAYS,
    EMA_FAST, EMA_SLOW,
    RSI_PERIOD, RSI_BUY_THRESHOLD,
    INITIAL_BALANCE, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    backtest, backtest_mean_reversion, backtest_breakout
)
from core.paper_broker import PaperBroker
from streamlit_autorefresh import st_autorefresh
from core.simulator import simulate_over_time, plot_price_and_equity

# Strategy functions
from strategies.ema import apply_ema_strategy as apply_ema_strategy
from strategies.rsi import apply_mean_reversion_strategy
from strategies.breakout import apply_breakout_strategy
from strategies.macd import apply_macd_strategy
from strategies.bollinger import apply_bollinger_strategy

# Page config
st.set_page_config(layout="wide", page_title="Crypto Strategy Dashboard")
st.title("📈 Crypto Strategy Dashboard")

# Load CSS
css_file = pathlib.Path("static/styles.css").read_text()
st.markdown(f"<style>{css_file}</style>", unsafe_allow_html=True)

# === Strategy Selector ===
strategy = st.sidebar.selectbox("Choose Strategy", [
    "EMA Crossover", "RSI Mean Reversion", "Breakout", "MACD", "Bollinger Bands",
    "RSI Screener", "Real-Time Signals", "Paper Trading 💸", "Simulate Strategy Over Time"
])



# === Market Settings Shared ===
coin_options = {
    "Bitcoin (BTC)": "bitcoin",
    "Ethereum (ETH)": "ethereum",
    "Solana (SOL)": "solana",
    "Cardano (ADA)": "cardano",
    "Dogecoin (DOGE)": "dogecoin"
}
selected_coin = st.sidebar.selectbox("Select Coin", list(coin_options.keys()), key="main_coin_selector")
coin = coin_options[selected_coin]
vs_currency = st.sidebar.text_input("Quote Currency", VS_CURRENCY)
days = st.sidebar.slider("Number of Days", 10, 90, int(DAYS))

# === Utility: Show Performance Table ===
def show_performance_table(trades_df, pnl, final_val, initial_balance):
    returns_pct = (final_val - initial_balance) / initial_balance * 100
    wins = trades_df[trades_df['action'].str.contains('SELL') & trades_df['price'] > trades_df.shift(1)['price']]
    losses = trades_df[trades_df['action'].str.contains('SELL') & trades_df['price'] <= trades_df.shift(1)['price']]
    total_trades = len(trades_df[trades_df['action'].str.contains('SELL')])
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    avg_win = wins['price'].pct_change().mean() * 100 if not wins.empty else 0
    avg_loss = losses['price'].pct_change().mean() * 100 if not losses.empty else 0

    metrics_df = pd.DataFrame({
        'Metric': ["Final Value", "Total PnL", "Return %", "# Trades", "Win Rate %", "Avg Win %", "Avg Loss %"],
        'Value': [
            f"${final_val:,.2f}",
            f"${pnl:,.2f}",
            f"{returns_pct:.2f}%",
            total_trades,
            f"{win_rate:.2f}%",
            f"{avg_win:.2f}%",
            f"{avg_loss:.2f}%"
        ]
    })
    st.subheader("Performance Metrics")
    st.dataframe(metrics_df, use_container_width=True)

# === Utility: Show Equity Curve and Drawdown ===
def show_equity_curve(df, trades_df, initial_balance):
    equity = []
    balance = initial_balance
    position = 0
    for i, row in df.iterrows():
        if not trades_df.empty and row['timestamp'] in trades_df['timestamp'].values:
            action = trades_df[trades_df['timestamp'] == row['timestamp']]['action'].values[0]
            price = row['close']
            if 'BUY' in action:
                position = balance / price
                balance = 0
            elif 'SELL' in action:
                balance = position * price
                position = 0
        equity_val = balance + position * row['close']
        equity.append(equity_val)

    df['equity'] = equity
    df['drawdown'] = df['equity'] / df['equity'].cummax() - 1

    # Buy and hold line
    df['buy_and_hold'] = initial_balance * df['close'] / df['close'].iloc[0]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
    ax1.plot(df['timestamp'], df['equity'], label='Equity Curve', linewidth=2)
    ax1.plot(df['timestamp'], df['buy_and_hold'], label='Buy & Hold Benchmark', linestyle='--')
    ax1.set_title('Equity Curve')
    ax1.legend()

    ax2.plot(df['timestamp'], df['drawdown'], label='Drawdown', color='red')
    ax2.set_title('Drawdown')
    ax2.legend()

    st.subheader("Equity Curve and Drawdown")
    st.pyplot(fig)

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
            try:
                df = fetch_ohlcv(coin, vs_currency, days)
                st.write("Initial DataFrame shape:", df.shape)
                st.write("Initial DataFrame columns:", df.columns.tolist())
                
                df = apply_ema_strategy(df, fast, slow, rsi_period, rsi_threshold)
                st.write("After strategy DataFrame shape:", df.shape)
                st.write("After strategy DataFrame columns:", df.columns.tolist())
                
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
                show_performance_table(trades_df, pnl, final_val, INITIAL_BALANCE)
                show_equity_curve(df, trades_df, INITIAL_BALANCE)
            except Exception as e:
                st.error(f"❌ An error occurred while processing data: {str(e)}")
                st.write("Error details:", e.__class__.__name__)

# === RSI Mean Reversion Strategy ===
if strategy == "RSI Mean Reversion":
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
                    show_performance_table(trades_df, pnl, final_val, INITIAL_BALANCE)
                    show_equity_curve(df, trades_df, INITIAL_BALANCE)
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
                    show_performance_table(trades_df, pnl, final_val, INITIAL_BALANCE)  
                    show_equity_curve(df, trades_df, INITIAL_BALANCE)
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
        show_performance_table(trades_df, pnl, final_val, INITIAL_BALANCE)
        show_equity_curve(df, trades_df, INITIAL_BALANCE)

# === Bollinger Bands Strategy ===
if strategy == "Bollinger Bands":
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
        show_performance_table(trades_df, pnl, final_val, INITIAL_BALANCE)
        show_equity_curve(df, trades_df, INITIAL_BALANCE)       

if strategy == "RSI Screener":
    st.header("📊 Multi-Ticker RSI Screener")
    rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)
    rsi_lower = st.sidebar.slider("Lower RSI Threshold", 10, 50, 30)
    rsi_upper = st.sidebar.slider("Upper RSI Threshold", 50, 90, 70)

    results = []
    for name, cid in coin_options.items():
        try:
            df = fetch_ohlcv(cid, VS_CURRENCY, DAYS)
            df["rsi"] = compute_rsi(df["close"], rsi_period)
            current_rsi = df["rsi"].iloc[-1]
            rsi_label = "🔥 Oversold" if current_rsi < rsi_lower else ("🚨 Overbought" if current_rsi > rsi_upper else "✅ Neutral")
            results.append({"Coin": name, "RSI": round(current_rsi, 2), "Signal": rsi_label})
        except Exception as e:
            results.append({"Coin": name, "RSI": "Error", "Signal": str(e)})

    screener_df = pd.DataFrame(results)
    st.dataframe(screener_df, use_container_width=True)


# === Real-Time Signal Dashboard ===
if strategy == "Real-Time Signals":
    st.header("\U0001F6A8 Real-Time Signal Dashboard")
    rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)
    ema_fast = st.sidebar.slider("Fast EMA", 5, 20, 9)
    ema_slow = st.sidebar.slider("Slow EMA", 10, 50, 21)
    show_only_signals = st.sidebar.checkbox("Show Only Coins with Signals", value=False)

    results = []
    for name, cid in coin_options.items():
        try:
            df = fetch_ohlcv(cid, vs_currency, days)
            df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
            df['rsi'] = compute_rsi(df['close'], rsi_period)
            latest = df.iloc[-1]

            signal = []
            if latest['ema_fast'] > latest['ema_slow']:
                signal.append("EMA Bullish")
            if latest['rsi'] < 30:
                signal.append("RSI Oversold")
            elif latest['rsi'] > 70:
                signal.append("RSI Overbought")

            signal_str = ", ".join(signal) or "Neutral"
            if show_only_signals and signal_str == "Neutral":
                continue

            results.append({"Coin": name, "Price": latest['close'], "EMA Fast": round(latest['ema_fast'], 2), "EMA Slow": round(latest['ema_slow'], 2), "RSI": round(latest['rsi'], 2), "Signal": signal_str})
        except Exception as e:
            results.append({"Coin": name, "Price": "Error", "EMA Fast": "-", "EMA Slow": "-", "RSI": "-", "Signal": str(e)})

    signal_df = pd.DataFrame(results)

    def highlight_signals(val):
        if isinstance(val, str) and ("Bullish" in val or "Oversold" in val):
            return 'background-color: #22c55e; color: black'
        elif isinstance(val, str) and "Overbought" in val:
            return 'background-color: #f87171; color: black'
        return ''

    styled_df = signal_df.style.applymap(highlight_signals, subset=['Signal'])
    st.dataframe(styled_df, use_container_width=True)

# === Paper Trading Module ===
if strategy == "Paper Trading 💸":
    st_autorefresh(interval=10000, limit=None, key="paper-refresh")
    st.header("💸 Paper Trading Simulator")

    if "broker" not in st.session_state:
        st.session_state.broker = PaperBroker(initial_balance=10000)
    broker = st.session_state.broker

    # === Select coin and get live price ===
    symbol_map = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD",
        "Cardano (ADA)": "ADA-USD",
    }
    selected = st.selectbox("Select Coin", list(symbol_map.keys()))
    symbol = symbol_map[selected]

    try:
        live_price = fetch_price(symbol)
        if live_price <= 0:
            raise ValueError("Invalid price received")
        st.success(f"Live price for {symbol}: ${live_price:.2f}")
    except Exception as e:
        st.error(f"Error fetching price: {str(e)}")
        live_price = broker.get_last_price(symbol) or 0.0

    # === Strategy selector ===
    strategy_choice = st.selectbox("Algorithmic Strategy", ["EMA", "RSI", "Breakout", "MACD", "Bollinger"])

    # === Sizing controls ===
    sizing_method = st.radio("Position Sizing", ["Fixed Quantity", "Percentage of Balance"])
    if sizing_method == "Fixed Quantity":
        qty = st.number_input("Trade Quantity", min_value=0.001, value=0.01)
    else:
        pct = st.slider("Percentage of Balance", 1, 100, 10)
        qty = (broker.get_balance() * (pct/100)) / live_price if live_price > 0 else 0
        st.write(f"Quantity: {qty:.4f}")

    # === Risk controls ===
    risk_type = st.radio("Stop Loss Type", ["Fixed Price", "Percentage"])
    if risk_type == "Fixed Price":
        stop_loss = st.number_input("Stop Loss Price", value=0.0)
    else:
        stop_pct = st.slider("Stop Loss %", 1, 20, 5)
        stop_loss = live_price * (1 - stop_pct/100) if live_price > 0 else 0
        st.write(f"Stop Loss Price: ${stop_loss:.2f}")

    take_profit = st.number_input("Optional Take-Profit Price", value=0.0)

    # === Signal logic ===
    coin_id_map = {
        "BTC-USD": "bitcoin",
        "ETH-USD": "ethereum",
        "SOL-USD": "solana",
        "ADA-USD": "cardano"
    }
    coin_id = coin_id_map[symbol]

    def get_strategy_signal(df, strategy_choice):
        if strategy_choice == "EMA":
            df = apply_ema_strategy(df)
            return df, df["signal"].iloc[-1]
        elif strategy_choice == "RSI":
            df = apply_mean_reversion_strategy(df, rsi_period=14, rsi_buy=25, rsi_sell=70)
            latest_rsi = df["rsi"].iloc[-1]
            signal = 1 if latest_rsi < 25 else -1 if latest_rsi > 70 else 0
            return df, signal
        elif strategy_choice == "Breakout":
            df = apply_breakout_strategy(df, window=20, volume_filter=False)
            return df, df["signal"].iloc[-1]
        elif strategy_choice == "MACD":
            df = apply_macd_strategy(df, fast=12, slow=26, signal=9)
            return df, df["signal"].iloc[-1]
        elif strategy_choice == "Bollinger":
            df = apply_bollinger_strategy(df, window=20, num_std=2)
            return df, df["signal"].iloc[-1]
        return df, 0

    try:
        df = fetch_ohlcv(coin_id, vs_currency=vs_currency, days=days)
        if df.empty:
            st.error("No data received")
            signal = 0
        else:
            df, signal = get_strategy_signal(df, strategy_choice)
            st.markdown(f"**Strategy Signal ({strategy_choice}):** `{signal}`")
    except Exception as e:
        st.error(f"Error calculating signal: {e}")
        signal = 0

    if signal == 1 and not broker.get_open_position():
        st.info("📈 Strategy triggered BUY")
        broker.buy(symbol, qty, live_price, sl=stop_loss if stop_loss > 0 else None, tp=take_profit if take_profit > 0 else None)
    elif signal == -1 and broker.get_open_position():
        st.info("📉 Strategy triggered SELL")
        broker.sell(symbol, live_price)

    # === Trade Controls ===
    st.markdown("### 🛠 Manual Trade Controls")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📈 Market Buy"):
            st.success(broker.buy(symbol, qty, live_price, sl=stop_loss if stop_loss > 0 else None, tp=take_profit if take_profit > 0 else None))

    with col2:
        if st.button("📉 Market Sell"):
            st.success(broker.sell(symbol, live_price))

    with col3:
        limit_price = st.number_input("Limit Price", min_value=1.0, value=live_price)
        side = st.radio("Limit Order Type", ["buy", "sell"])
        if st.button("📝 Place Limit Order"):
            st.success(broker.place_limit_order(symbol, qty, limit_price, side))

    # === Trigger checks ===
    triggered_sl_tp = broker.check_stop_loss_take_profit(live_price)
    if triggered_sl_tp:
        st.warning(triggered_sl_tp)

    order_fills = broker.check_orders(live_price)
    for msg in order_fills:
        st.info(msg)

    # === Display Info ===
    st.markdown("---")
    st.write("💰 **Balance:**", f"${broker.get_balance():,.2f}")
    pos = broker.get_open_position()
    if pos:
        st.write("📈 **Open Position:**", pos)
        pnl = broker.get_unrealized_pnl(live_price)
        st.write(f"📈 **Unrealized PnL:** ${pnl:.2f}")

    st.subheader("📜 Trade Log")
    st.dataframe(pd.DataFrame(broker.get_trade_log()))

    st.subheader("🧾 Open Orders")
    st.dataframe(pd.DataFrame(broker.get_open_orders()))

    # === Export/Reset ===
    st.markdown("---")
    st.subheader("🧾 Trade Log Controls")
    col1, col2 = st.columns(2)
    trades_df = pd.DataFrame(broker.get_trade_log())
    if not trades_df.empty:
        trades_df.to_csv("paper_trades.csv", index=False)

    with col1:
        if os.path.exists("paper_trades.csv") and not trades_df.empty:
            with open("paper_trades.csv", "rb") as f:
                st.download_button("📥 Download Trade Log (CSV)", f, file_name="paper_trades.csv", mime="text/csv")
        else:
            st.write("No trades to download")

    with col2:
        if st.button("🗑️ Clear Trade Log"):
            broker.trades.clear()
            if os.path.exists("paper_trades.csv"):
                os.remove("paper_trades.csv")
            st.success("Trade log cleared successfully!")

# === Simulate Strategy Over Time ===
if strategy == "Simulate Strategy Over Time":
    st.header("⏳ Strategy Simulation Over Time")

    # Add a unique key to this selectbox
    selected_coin = st.sidebar.selectbox(
        "Select Coin", 
        list(coin_options.keys()), 
        key="simulation_coin_selector"
    )
    coin_id = coin_options[selected_coin]

    # Add unique keys to other widgets too
    position_size = st.number_input(
        "Position Size (quantity)", 
        min_value=0.001, 
        value=0.01, 
        step=0.001,
        key="sim_position_size"
    )
    
    sl_pct = st.slider(
        "Stop Loss %", 
        0, 20, 5, 
        key="sim_sl_pct"
    ) / 100
    
    tp_pct = st.slider(
        "Take Profit %", 
        0, 50, 10, 
        key="sim_tp_pct"
    ) / 100

    strat_name = st.selectbox(
        "Choose Strategy", 
        ["EMA", "MACD", "RSI", "Breakout"],
        key="sim_strategy_select"
    )
    
    if strat_name == "EMA":
        fast = st.slider("Fast EMA", 5, 50, 12)
        slow = st.slider("Slow EMA", 10, 100, 26)
        rsi_period = st.slider("RSI Period", 5, 30, 14)
        rsi_threshold = st.slider("RSI Buy Threshold", 10, 50, 30)
        def strategy_func(df):
            return apply_ema_strategy(df, fast, slow, rsi_period, rsi_threshold)
    elif strat_name == "MACD":
        def strategy_func(df):
            return apply_macd_strategy(df, fast=12, slow=26, signal=9)
    elif strat_name == "RSI":
        rsi_period = st.slider("RSI Period", 5, 30, 14)
        rsi_buy = st.slider("RSI Buy", 10, 40, 30)
        rsi_sell = st.slider("RSI Sell", 60, 90, 70)
        def strategy_func(df):
            return apply_mean_reversion_strategy(df, rsi_period, rsi_buy, rsi_sell)
    elif strat_name == "Breakout":
        window = st.slider("Lookback Window", 5, 50, 20)
        def strategy_func(df):
            return apply_breakout_strategy(df, window=window, volume_filter=False)

    if st.button("▶️ Run Simulation"):
        with st.spinner(f"Fetching data for {coin_id}..."):
            try:
                st.write(f"Fetching data for {coin_id}")
                df = fetch_ohlcv(coin_id, vs_currency=vs_currency, days=days)
                
                if df.empty:
                    st.error("No data received")
                    st.write(f"Parameters used:")
                    st.write(f"- coin_id: {coin_id}")
                    st.write(f"- vs_currency: {vs_currency}")
                    st.write(f"- days: {days}")
                else:
                    sim_broker = PaperBroker(initial_balance=10000)
                    
                    # Calculate stop loss and take profit prices based on current price
                    current_price = df['close'].iloc[-1]
                    sl = current_price * (1 - sl_pct) if sl_pct > 0 else None
                    tp = current_price * (1 + tp_pct) if tp_pct > 0 else None
                    
                    trades, df = simulate_over_time(
                        df=df,
                        strategy_func=strategy_func,
                        broker=sim_broker,
                        symbol=selected_coin.upper() + "-USD",
                        position_size=position_size,
                        sl=sl,
                        tp=tp,
                        verbose=True  # Enable verbose mode for debugging
                    )

                    if trades:
                        st.success(f"Simulation complete: {len(trades)} trades executed.")
                        trades_df = pd.DataFrame(trades)
                        st.dataframe(trades_df)
                        final_balance = sim_broker.get_balance()
                        pnl = final_balance - 10000
                        st.metric("Final Balance", f"${final_balance:,.2f}", f"{pnl:+,.2f}")
                        
                        plot_price_and_equity(df, trades)
                        
                        # Show performance metrics
                        if len(trades) > 0:
                            show_performance_table(trades_df, pnl, final_balance, 10000)
                    else:
                        st.warning("No trades were executed during the simulation period.")
                        
            except Exception as e:
                st.error(f"Error during simulation: {str(e)}")

