# Crypto EMA Crossover Backtester

This is a basic backtester for a crypto trading strategy using an EMA crossover system.

## 📈 Strategy Logic
- Buy when EMA(5) crosses above EMA(10)
- Sell when EMA(5) crosses below EMA(10)
- Uses Binance historical data (BTC/USDT 1h candles)

## 🛠 Features
- Fetches price data from Binance
- Executes simulated trades
- Logs trades to `trades.csv`
- Saves a price/EMA plot to `chart.png`

## 🚀 How to Run

1. Clone the repo
2. Set up a virtual environment (optional)
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Run:
    ```bash
    python crypto_backtester.py
    ```

## 🧠 TODO
- Add RSI filter
- Add stop-loss/take-profit logic
- Live paper trading support
