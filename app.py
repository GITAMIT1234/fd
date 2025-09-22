import streamlit as st
import pandas as pd
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval
from io import BytesIO
import base64

st.title("📊 TradingView Data Downloader (1500 Daily Bars with Volume)")

# --- LOGIN SECTION ---
username = st.text_input("Enter TradingView Username/Email")
password = st.text_input("Enter TradingView Password", type="password")

if st.button("Login"):
    try:
        st.session_state.tv = TvDatafeed(username, password)
        st.success("✅ Logged in successfully!")
    except Exception as e:
        st.error(f"❌ Login failed: {e}")

# --- SYMBOL INPUT ---
symbols_input = st.text_area("Enter stock symbols (comma separated):", "RELIANCE, TCS, INFY")
symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]
exchange = st.selectbox("Select Exchange", ["NSE", "BSE"], index=0)

# --- FETCH & DOWNLOAD ---
if st.button("Download Data (1500 Days)"):
    if "tv" not in st.session_state:
        st.error("⚠️ Please login first!")
    else:
        tv = st.session_state.tv
        all_data = []

        progress = st.progress(0)

        for i, symbol in enumerate(symbols, start=1):
            try:
                # ✅ Fetch last 1500 daily candles
                df = tv.get_hist(
                    symbol=symbol,
                    exchange=exchange,
                    interval=Interval.in_daily,  # Fixed to daily only
                    n_bars=1500
                )

                if df is None or df.empty:
                    st.warning(f"No data for {symbol}")
                else:
                    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
                    df.reset_index(inplace=True)
                    df.rename(columns={
                        'datetime': 'Date',
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    }, inplace=True)
                    df.insert(0, "Symbol", symbol)
                    all_data.append(df)

            except Exception as e:
                st.error(f"Error fetching {symbol}: {e}")

            progress.progress(i / len(symbols))

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            st.subheader("📥 Download Data (1500 Trading Days with Volume)")

            # Save Excel
            buffer_xlsx = BytesIO()
            with pd.ExcelWriter(buffer_xlsx, engine="openpyxl") as writer:
                final_df.to_excel(writer, index=False, sheet_name="StockData")
            buffer_xlsx.seek(0)
            b64_xlsx = base64.b64encode(buffer_xlsx.read()).decode()
            filename_xlsx = f"StockData_{datetime.today().strftime('%Y-%m-%d')}.xlsx"
            st.markdown(
                f'<a href="data:application/octet-stream;base64,{b64_xlsx}" '
                f'download="{filename_xlsx}">📊 Download Excel (1500 Days)</a>',
                unsafe_allow_html=True
            )

            # Save CSV
            csv = final_df.to_csv(index=False).encode()
            b64_csv = base64.b64encode(csv).decode()
            filename_csv = f"StockData_{datetime.today().strftime('%Y-%m-%d')}.csv"
            st.markdown(
                f'<a href="data:file/csv;base64,{b64_csv}" '
                f'download="{filename_csv}">📄 Download CSV (1500 Days)</a>',
                unsafe_allow_html=True
            )
        else:
            st.warning("No data available for download.")
