#import streamlit as st
import yfinance as yf
import talib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
import streamlit as st

TA_LIB_PATH = "/usr/lib/libta_lib.so"

def install_talib():
    st.warning("Building TA-Lib (this runs once, may take 1–2 minutes)...")

    cmd = """
    set -e

    echo "Downloading TA-Lib source..."
    wget -O ta-lib.tar.gz https://downloads.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz

    echo "Extracting..."
    tar -xzf ta-lib.tar.gz

    cd ta-lib

    echo "Configuring..."
    ./configure --prefix=/usr --disable-shared --enable-static

    echo "Building (low resource mode)..."
    make -j1

    echo "Installing..."
    make install
    """

    subprocess.run(
        ["bash", "-c", cmd],
        check=True
    )

if not os.path.exists(TA_LIB_PATH):
    install_talib()

import talib




# =====================
# Pattern Classification
# =====================
BREAKOUT_PATTERNS = [
    'CDLMARUBOZU','CDLOPENINGMARUBOZU','CDLCLOSINGMARUBOZU',
    'CDLLONGLINE','CDLBREAKAWAY','CDLKICKING','CDLKICKINGBYLENGTH'
]

REVERSAL_PATTERNS = [
    'CDLHAMMER','CDLINVERTEDHAMMER','CDLSHOOTINGSTAR','CDLHANGINGMAN',
    'CDLENGULFING','CDLDARKCLOUDCOVER','CDLMORNINGSTAR',
    'CDLEVENINGSTAR','CDLPIERCING','CDLTRISTAR'
]

CONTINUATION_PATTERNS = [
    'CDLRISING3METHODS','CDLFALLING3METHODS',
    'CDLSEPARATINGLINES','CDLXSIDEGAP3METHODS'
]

RANGE_PATTERNS = [
    'CDLDOJI','CDLSPINNINGTOP','CDLLONGLEGGEDDOJI',
    'CDLGRAVESTONEDOJI','CDLDRAGONFLYDOJI'
]

ALL_PATTERNS = BREAKOUT_PATTERNS + REVERSAL_PATTERNS + CONTINUATION_PATTERNS + RANGE_PATTERNS


def detect_patterns(df):
    results = []
    for p in ALL_PATTERNS:
        func = getattr(talib, p)
        signal = func(df['Open'], df['High'], df['Low'], df['Close'])
        df[p] = signal

        if signal.iloc[-1] != 0:
            results.append({
                'Pattern': p,
                'Signal': signal.iloc[-1],
                'Category': (
                    'Breakout' if p in BREAKOUT_PATTERNS else
                    'Reversal' if p in REVERSAL_PATTERNS else
                    'Continuation' if p in CONTINUATION_PATTERNS else
                    'Range'
                )
            })
    return df, results


# =====================
# Streamlit UI
# =====================
st.title("📊 TA-Lib 型態自動分類掃描器")

symbols = st.text_input("股票代碼（逗號分隔）", "TSLA,NVDA,AAPL")
interval = st.selectbox("K 線週期", ["5m", "15m", "1d"])

if st.button("開始掃描"):
    all_results = []

    for sym in symbols.split(","):
        stock = yf.Ticker(sym.strip())
        df = stock.history(period="1mo", interval=interval).reset_index()
        #df = yf.history(sym.strip(), period="30d", interval=interval)

        if len(df) < 20:
            continue

        df, patterns = detect_patterns(df)

        for p in patterns:
            p["Symbol"] = sym
            p["Close"] = df['Close'].iloc[-1]
            all_results.append(p)

        # 畫圖
        st.subheader(f"{sym} K 線圖")
        fig, ax = plt.subplots()
        ax.plot(df.index, df['Close'], label='Close')
        ax.set_title(sym)
        st.pyplot(fig)

    if all_results:
        result_df = pd.DataFrame(all_results)
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ 下載 CSV",
            csv,
            "ta_pattern_scan.csv",
            "text/csv"
        )
    else:
        st.warning("未偵測到有效型態")
