import streamlit as st
import pandas as pd
from core.fetch import fetch_ohlcv
from core.indicators import compute_rsi
from typing import List, Dict

def get_screener_params() -> Dict:
    """Get screener parameters from the sidebar."""
    with st.sidebar.form("screener_form"):
        st.header("Screener Parameters")
        params = {
            "rsi_period": st.slider("RSI Period", 5, 30, 14),
            "rsi_oversold": st.slider("RSI Oversold", 10, 40, 30),
            "rsi_overbought": st.slider("RSI Overbought", 60, 90, 70),
            "min_volume": st.number_input("Min 24h Volume ($)", 1000, 1000000000, 1000000),
            "days": st.slider("Lookback Days", 1, 30, 7)
        }
        submitted = st.form_submit_button("Run Screener")
        return params, submitted

def screen_coins(coins: List[str], vs_currency: str, params: Dict) -> pd.DataFrame:
    """Screen coins based on RSI criteria."""
    results = []
    
    for coin in coins:
        try:
            df = fetch_ohlcv(coin, vs_currency, params["days"])
            if df.empty:
                continue
                
            rsi = compute_rsi(df['close'], params["rsi_period"])
            current_rsi = rsi.iloc[-1]
            current_price = df['close'].iloc[-1]
            volume_24h = df['volume'].iloc[-1] * current_price
            
            if volume_24h < params["min_volume"]:
                continue
                
            signal = "Oversold" if current_rsi < params["rsi_oversold"] else \
                     "Overbought" if current_rsi > params["rsi_overbought"] else "Neutral"
                     
            results.append({
                "Coin": coin.upper(),
                "Price": f"${current_price:.2f}",
                "RSI": f"{current_rsi:.1f}",
                "24h Volume": f"${volume_24h:,.0f}",
                "Signal": signal
            })
            
        except Exception as e:
            st.warning(f"Error processing {coin}: {str(e)}")
            continue
            
    return pd.DataFrame(results)

def show_screener():
    """Display the RSI screener page."""
    st.header("📊 RSI Screener")
    
    # Get list of coins to screen
    coin_input = st.text_area(
        "Enter coin IDs to screen (comma-separated)", 
        value="bitcoin,ethereum,cardano,solana,polkadot,chainlink"
    )
    coins = [c.strip().lower() for c in coin_input.split(",") if c.strip()]
    
    # Get screener parameters
    params, submitted = get_screener_params()
    
    if submitted:
        with st.spinner("Screening coins..."):
            try:
                results_df = screen_coins(coins, "usd", params)
                
                if results_df.empty:
                    st.warning("No coins matched the screening criteria.")
                else:
                    # Style the dataframe
                    def color_signal(val):
                        if val == "Oversold":
                            return "background-color: #c6efce; color: #006100"
                        elif val == "Overbought":
                            return "background-color: #ffc7ce; color: #9c0006"
                        return ""
                    
                    styled_df = results_df.style.applymap(
                        color_signal, 
                        subset=['Signal']
                    )
                    
                    st.dataframe(
                        styled_df,
                        use_container_width=True
                    )
                    
                    # Download button
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        "Download Results",
                        csv,
                        "screener_results.csv",
                        "text/csv",
                        key='download-csv'
                    )
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Enter coins and click **Run Screener** to start screening.") 