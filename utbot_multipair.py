#PUSHOVER_USER_KEY = "uyx2dq5c3aunrf6ctxqxa3whjzvaf7"
#PUSHOVER_API_TOKEN = "ann22xinwtuhgjf9ouww6xn1noxec7"

import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests

# ----------------------------------
# CONFIG
# ----------------------------------
PUSHOVER_USER_KEY = "uyx2dq5c3aunrf6ctxqxa3whjzvaf7"
PUSHOVER_API_TOKEN = "ann22xinwtuhgjf9ouww6xn1noxec7"

KEY_VALUE = 2
ATR_PERIOD = 1
EMA_PERIOD = 200
TIMEFRAME = "15m"

# Pairs to monitor
PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "USDCHF": "CHF=X",
    "NZDJPY": "NZDJPY=X",
    "AUDCAD": "AUDCAD=X",
    "CHFJPY": "CHFJPY=X"
}


# ----------------------------------
# SEND ALERT
# ----------------------------------
def send_alert(pair, msg):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": msg,
            "title": f"UT BOT ALERT | {pair}"
        }
    )


# ----------------------------------
# UT BOT LOGIC
# ----------------------------------
def compute_utbot(df):

    # If multi-index columns (Yahoo bug), flatten them
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    df["H-L"] = df["High"] - df["Low"]
    df["H-C"] = abs(df["High"] - df["Close"].shift())
    df["L-C"] = abs(df["Low"] - df["Close"].shift())
    df["TR"] = df[["H-L", "H-C", "L-C"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(ATR_PERIOD).mean()

    df["xATRTrailingStop"] = df["Close"] - (KEY_VALUE * df["ATR"])
    df["EMA"] = df["Close"].ewm(span=EMA_PERIOD, adjust=False).mean()

    df["Buy"] = (
        (df["Close"] > df["xATRTrailingStop"]) &
        (df["Close"].shift() < df["xATRTrailingStop"].shift())
    )

    df["Sell"] = (
        (df["Close"] < df["xATRTrailingStop"]) &
        (df["Close"].shift() > df["xATRTrailingStop"].shift())
    )

    return df


# ----------------------------------
# MAIN LOOP
# ----------------------------------
print("🔄 MULTI-PAIR UT BOT RUNNING (15m)...")

while True:
    try:
        for pair_name, ticker in PAIRS.items():
            print(f"\nChecking {pair_name}...")

            df = yf.download(ticker, interval=TIMEFRAME, period="7d", auto_adjust=False)

            if df.empty:
                print(f"⚠ No data returned for {pair_name}")
                continue

            df = compute_utbot(df)
            last = df.iloc[-1]

            # BUY signal
            if last["Buy"]:
                send_alert(pair_name, f"BUY Signal {pair_name} 15m\nPrice: {last['Close']:.5f}")
                print(f"🚀 BUY alert sent for {pair_name}")

            # SELL signal
            if last["Sell"]:
                send_alert(pair_name, f"SELL Signal {pair_name} 15m\nPrice: {last['Close']:.5f}")
                print(f"🔥 SELL alert sent for {pair_name}")

        # Wait 60 seconds before next scan
        print("\n⏳ Waiting 60 seconds before next scan...\n")
        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        print("Retrying in 10 seconds...")
        time.sleep(10)
