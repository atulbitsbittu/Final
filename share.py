# Save this as banknifty_dashboard.py

import yfinance as yf
import pandas as pd
import streamlit as st
import ta
from datetime import datetime, timedelta

# --------- Parameters ---------
symbol = "^NSEBANK"  # Bank Nifty Index
timeframes = {"5m": "5m", "15m": "15m", "1h": "60m"}
lookback_period = "7d"

# --------- Functions ---------
@st.cache_data(ttl=3600)
def get_data(interval):
    data = yf.download(symbol, period=lookback_period, interval=interval)
    return data.dropna()

def add_technical_indicators(df):
    close_series = df["Close"].squeeze()

    # Calculate indicators
    rsi = ta.momentum.RSIIndicator(close=close_series).rsi()
    macd = ta.trend.MACD(close=close_series).macd_diff()
    ema_20 = ta.trend.EMAIndicator(close=close_series, window=20).ema_indicator()

    # Assign indicators
    df["rsi"] = rsi
    df["macd"] = macd
    df["ema_20"] = ema_20

    # Ensure ema_signal is aligned and not NaN
    df["ema_signal"] = (df["Close"] > df["ema_20"])
    df["ema_signal"] = df["ema_signal"].fillna(False)

    return df

def generate_signal(row):
    if row["rsi"] < 30 and row["macd"] > 0 and row["ema_signal"]:
        return "Buy"
    elif row["rsi"] > 70 and row["macd"] < 0 and not row["ema_signal"]:
        return "Sell"
    else:
        return "Hold"

def dummy_fundamental_sentiment_score():
    # Placeholder: 1 = Bullish, -1 = Bearish, 0 = Neutral
    return 1  # Simulate bullish sentiment

def accuracy_tracking(df):
    df["Signal"] = df.apply(generate_signal, axis=1)

    # Prevent accuracy NaNs due to future close
    df = df[:-2]
    df["Future Close"] = df["Close"].shift(-2)

    df["Correct"] = ((df["Signal"] == "Buy") & (df["Future Close"] > df["Close"])) | \
                    ((df["Signal"] == "Sell") & (df["Future Close"] < df["Close"]))

    accuracy = df["Correct"].mean() * 100
    return df, round(accuracy, 2)

# --------- Streamlit UI ---------
st.set_page_config("Bank Nifty Signal Dashboard", layout="wide")
st.title("📊 Bank Nifty Signal Dashboard")

for label, interval in timeframes.items():
    st.subheader(f"⏱ Timeframe: {label}")

    data = get_data(interval)
    data = add_technical_indicators(data)
    score = dummy_fundamental_sentiment_score()

    # Apply sentiment impact to final signal
    data["Signal"] = data.apply(generate_signal, axis=1)
    if score == 1:
        data.loc[data["Signal"] == "Hold", "Signal"] = "Buy"
    elif score == -1:
        data.loc[data["Signal"] == "Hold", "Signal"] = "Sell"

    # Accuracy tracking
    data, acc = accuracy_tracking(data)

    # Display signal + accuracy
    st.markdown(f"✅ **Signal Accuracy:** `{acc}%`")
    st.dataframe(
        data[["Close", "rsi", "macd", "Signal"]].tail(10).style.applymap(
            lambda x: "color: green" if x == "Buy" else "color: red" if x == "Sell" else "color: gray", 
            subset=["Signal"]
        )
    )
