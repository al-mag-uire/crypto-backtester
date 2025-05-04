# 🧠 Crypto Strategy Dashboard

An interactive Streamlit-based crypto backtesting and signal generation dashboard. Includes several algorithmic strategies (EMA Crossover, RSI Mean Reversion, Breakout, MACD, Bollinger Bands) with historical backtesting, performance metrics, and real-time signal detection.

---

## 🚀 Features

- 📈 Visual backtests with trade markers and equity curves
- 🧪 Built-in strategy performance metrics
- 🛠 Real-time signal screener across multiple coins
- 📊 Compare strategy vs. buy & hold
- ⚙️ Fully modular architecture for easy strategy development

---

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
