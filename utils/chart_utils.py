import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def plot_strategy_indicators(df: pd.DataFrame, strategy: str) -> None:
    """Plot strategy-specific indicators and signals."""
    plt.style.use('dark_background')
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
    
    # Use index for x-axis if no timestamp column
    x_axis = df.index if 'timestamp' not in df.columns else df['timestamp']
    
    # Price chart (common for all strategies)
    ax1.plot(x_axis, df['close'], label='Price', color='#1E88E5', alpha=0.8)
    
    # Plot buy/sell signals
    buy_points = df[df['signal'] == 1]
    sell_points = df[df['signal'] == -1]
    
    # Use index for signals
    buy_x = buy_points.index if 'timestamp' not in df.columns else buy_points['timestamp']
    sell_x = sell_points.index if 'timestamp' not in df.columns else sell_points['timestamp']
    
    ax1.scatter(buy_x, buy_points['close'], 
                color='#00E676', marker='^', label='Buy Signal', s=100)
    ax1.scatter(sell_x, sell_points['close'], 
                color='#FF3D00', marker='v', label='Sell Signal', s=100)
    
    # Strategy-specific indicators
    if strategy.lower() == "rsi":
        ax2.plot(x_axis, df['rsi'], label='RSI', color='#B388FF')
        ax2.axhline(y=30, color='#00E676', linestyle='--', alpha=0.5, label='Buy Level (30)')
        ax2.axhline(y=70, color='#FF3D00', linestyle='--', alpha=0.5, label='Sell Level (70)')
        ax2.axhline(y=50, color='gray', linestyle='-', alpha=0.2)
        ax2.fill_between(x_axis, df['rsi'], 30, where=(df['rsi'] <= 30), 
                        color='#00E676', alpha=0.1)
        ax2.fill_between(x_axis, df['rsi'], 70, where=(df['rsi'] >= 70), 
                        color='#FF3D00', alpha=0.1)
        ax2.set_ylim(0, 100)
        ax2.set_title('RSI Indicator')
        
    elif strategy.lower() == "macd":
        # Reference from strategies/macd.py lines 169-175
        ax2.plot(x_axis, df['macd'], label='MACD', color='blue')
        ax2.plot(x_axis, df['macd_signal'], label='Signal', color='orange')
        ax2.bar(x_axis, df['hist'], label='Histogram', color='gray', alpha=0.3)
        ax2.axhline(0, color='gray', linestyle='--', alpha=0.3)
        ax2.set_title('MACD')
        
    elif strategy.lower() == "ema":
        # Reference from views/strategy_backtest.py lines 124-126
        ax1.plot(x_axis, df['ema_fast'], label='Fast EMA')
        ax1.plot(x_axis, df['ema_slow'], label='Slow EMA')
        ax2.plot(x_axis, df['rsi'], label='RSI', color='purple')
        ax2.axhline(30, color='red', linestyle='--', label='RSI 30')
        ax2.axhline(70, color='green', linestyle='--', label='RSI 70')
        ax2.set_ylim(0, 100)
        ax2.set_title('RSI')
        
    elif strategy.lower() == "bollinger":
        ax1.plot(x_axis, df['middle_band'], label='Middle Band', color='yellow', alpha=0.7)
        ax1.plot(x_axis, df['upper_band'], label='Upper Band', color='red', alpha=0.7)
        ax1.plot(x_axis, df['lower_band'], label='Lower Band', color='green', alpha=0.7)
        ax1.fill_between(x_axis, df['upper_band'], df['lower_band'], alpha=0.1, color='gray')
        
        # Price distance from middle band
        ax2.plot(x_axis, (df['close'] - df['middle_band']) / df['middle_band'] * 100, 
                label='% Distance from Middle Band', color='purple')
        ax2.axhline(0, color='yellow', linestyle='--', alpha=0.5)
        ax2.set_title('Price Distance from Middle Band (%)')
        
    elif strategy.lower() == "breakout":
        ax1.plot(x_axis, df['rolling_high'], label='Rolling High', color='green', alpha=0.7)
        ax1.plot(x_axis, df['rolling_low'], label='Rolling Low', color='red', alpha=0.7)
        ax1.fill_between(x_axis, df['rolling_high'], df['rolling_low'], alpha=0.1, color='gray')
        
        # Price momentum
        ax2.plot(x_axis, df['close'].pct_change(periods=5) * 100, 
                label='Price Momentum (5-period)', color='blue')
        ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
        ax2.set_title('Price Momentum (%)')
    
    # Common styling
    ax1.grid(True, alpha=0.2)
    ax1.legend(loc='upper left')
    ax2.grid(True, alpha=0.2)
    ax2.legend(loc='upper left')
    ax1.set_title('Price and Trading Signals')
    
    # Adjust layout
    plt.tight_layout()
    
    # Display
    st.pyplot(fig)

def display_strategy_metrics(df: pd.DataFrame, strategy_params: dict) -> None:
    """Display strategy parameters and signal counts."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Strategy Parameters:", strategy_params)
    
    with col2:
        buy_signals = len(df[df['signal'] == 1])
        sell_signals = len(df[df['signal'] == -1])
        st.metric("Buy Signals", buy_signals)
        st.metric("Sell Signals", sell_signals) 