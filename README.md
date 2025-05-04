# Crypto Strategy Backtester Dashboard

This project is a **multi-strategy crypto trading dashboard** built with **Streamlit** and **Python**, designed for backtesting popular algorithmic trading strategies using historical price data from CoinGecko.

## 🚀 Features
- Interactive dashboard with sidebar parameter tuning
- Real-time charting and trade visualization
- Strategy-specific forms and logic
- Trade logs with detailed entry/exit prices

## 📈 Supported Strategies
- **EMA Crossover** with RSI Filter and SL/TP
- **RSI Mean Reversion** with RSI thresholds and SL/TP
- **Breakout Strategy** (with optional volume filter)
- **MACD Crossover**
- **Bollinger Bands**

## ⚙️ How to Run
```bash
# Clone the repo
git clone https://github.com/your-username/crypto-backtester.git
cd crypto-backtester

# (Optional) Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

## 📊 Example Output
- Strategy-specific performance summary
- Trade markers (buy/sell arrows)
- RSI or indicator overlays

## 🔧 Customize
Each strategy is modular and defined in `crypto_backtester.py`. You can:
- Add new indicators
- Change entry/exit logic
- Extend backtests to include slippage, fees, etc.

## 📡 Data Source
Powered by the free CoinGecko API — no API key needed.

## 📘 License
MIT License

---

Want to deploy it online? Check out [Streamlit Community Cloud](https://streamlit.io/cloud).
