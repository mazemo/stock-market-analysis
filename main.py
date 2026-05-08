import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Market Analysis",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Stock Market Analysis System")
st.markdown("---")

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    symbol = st.text_input("Enter Stock Symbol", value="AAPL", max_chars=10).upper().strip()
    period = st.selectbox("Select Time Period", ["7 days", "1 month", "3 months", "6 months", "1 year"])
    chart_type = st.selectbox("Chart Type", ["Line Chart", "Candlestick Chart"])
    show_ma = st.checkbox("Show Moving Average (7-day)", value=True)
    show_volume = st.checkbox("Show Volume", value=True)
    search_btn = st.button("🔍 Fetch Data", use_container_width=True)

# ─── Period Mapping ─────────────────────────────────────────────────────────────
period_map = {
    "7 days":   "7d",
    "1 month":  "1mo",
    "3 months": "3mo",
    "6 months": "6mo",
    "1 year":   "1y",
}

# ─── Helper: Fetch Data ─────────────────────────────────────────────────────────
def fetch_stock(sym, period_str):
    ticker = yf.Ticker(sym)
    hist   = ticker.history(period=period_str)
    info   = ticker.info
    return ticker, hist, info

# ─── Helper: Metric Card ────────────────────────────────────────────────────────
def metric(label, value, delta=None):
    st.metric(label=label, value=value, delta=delta)

# ─── Main Logic ─────────────────────────────────────────────────────────────────
if search_btn or symbol:
    if not symbol:
        st.error("⚠️ Please enter a stock symbol.")
    else:
        with st.spinner(f"Fetching data for **{symbol}**..."):
            try:
                ticker, hist, info = fetch_stock(symbol, period_map[period])

                if hist.empty:
                    st.error(f"❌ No data found for symbol **{symbol}**. Please check and try again.")
                else:
                    # ── Company Header ────────────────────────────────────────
                    company_name = info.get("longName", symbol)
                    sector       = info.get("sector", "N/A")
                    industry     = info.get("industry", "N/A")
                    country      = info.get("country", "N/A")

                    st.subheader(f"🏢 {company_name}  (`{symbol}`)")
                    st.caption(f"📌 {sector} | {industry} | {country}")
                    st.markdown("---")

                    # ── Key Metrics ───────────────────────────────────────────
                    curr_price  = hist["Close"].iloc[-1]
                    prev_price  = hist["Close"].iloc[-2] if len(hist) > 1 else curr_price
                    change      = curr_price - prev_price
                    change_pct  = (change / prev_price) * 100
                    high_52w    = info.get("fiftyTwoWeekHigh", "N/A")
                    low_52w     = info.get("fiftyTwoWeekLow",  "N/A")
                    mkt_cap     = info.get("marketCap", None)
                    mkt_cap_str = f"${mkt_cap/1e9:.2f}B" if mkt_cap else "N/A"

                    c1, c2, c3, c4, c5 = st.columns(5)
                    with c1: metric("💰 Current Price",  f"${curr_price:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
                    with c2: metric("📅 Period High",     f"${hist['High'].max():.2f}")
                    with c3: metric("📅 Period Low",      f"${hist['Low'].min():.2f}")
                    with c4: metric("📆 52W High",        f"${high_52w}" if isinstance(high_52w, str) else f"${high_52w:.2f}")
                    with c5: metric("🏦 Market Cap",      mkt_cap_str)

                    st.markdown("---")

                    # ── Moving Average ────────────────────────────────────────
                    hist["MA7"] = hist["Close"].rolling(window=7).mean()
                    hist["Daily Change"] = hist["Close"].diff()

                    # ── Chart ─────────────────────────────────────────────────
                    rows  = 2 if show_volume else 1
                    specs = [[{"secondary_y": False}]] * rows
                    fig   = make_subplots(rows=rows, cols=1,
                                         shared_xaxes=True,
                                         row_heights=[0.7, 0.3] if show_volume else [1],
                                         vertical_spacing=0.05,
                                         specs=specs)

                    if chart_type == "Line Chart":
                        fig.add_trace(go.Scatter(
                            x=hist.index, y=hist["Close"],
                            mode="lines", name="Close Price",
                            line=dict(color="#00C8FF", width=2)
                        ), row=1, col=1)
                    else:
                        fig.add_trace(go.Candlestick(
                            x=hist.index,
                            open=hist["Open"], high=hist["High"],
                            low=hist["Low"],   close=hist["Close"],
                            name="OHLC",
                            increasing_line_color="#26a69a",
                            decreasing_line_color="#ef5350"
                        ), row=1, col=1)

                    if show_ma and len(hist) >= 7:
                        fig.add_trace(go.Scatter(
                            x=hist.index, y=hist["MA7"],
                            mode="lines", name="7-Day MA",
                            line=dict(color="#FFA500", width=1.5, dash="dash")
                        ), row=1, col=1)

                    if show_volume:
                        colors = ["#26a69a" if d >= 0 else "#ef5350" for d in hist["Daily Change"]]
                        fig.add_trace(go.Bar(
                            x=hist.index, y=hist["Volume"],
                            name="Volume", marker_color=colors, opacity=0.7
                        ), row=2, col=1)

                    fig.update_layout(
                        title=f"{company_name} — Price Trend ({period})",
                        xaxis_rangeslider_visible=False,
                        height=550,
                        template="plotly_dark",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=40, r=40, t=60, b=40)
                    )
                    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
                    if show_volume:
                        fig.update_yaxes(title_text="Volume", row=2, col=1)

                    st.plotly_chart(fig, use_container_width=True)

                    # ── Historical Data Table ─────────────────────────────────
                    with st.expander("📋 View Raw Historical Data"):
                        display_df = hist[["Open","High","Low","Close","Volume"]].copy()
                        display_df.index = display_df.index.strftime("%Y-%m-%d")
                        display_df = display_df.sort_index(ascending=False)
                        display_df.columns = ["Open","High","Low","Close","Volume"]
                        for col in ["Open","High","Low","Close"]:
                            display_df[col] = display_df[col].map("${:.2f}".format)
                        display_df["Volume"] = display_df["Volume"].map("{:,.0f}".format)
                        st.dataframe(display_df, use_container_width=True)

                    # ── About ─────────────────────────────────────────────────
                    summary = info.get("longBusinessSummary", "")
                    if summary:
                        with st.expander("ℹ️ About the Company"):
                            st.write(summary)

            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
                st.info("💡 Make sure you entered a valid stock ticker symbol (e.g., AAPL, TSLA, GOOGL).")

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("📊 Data provided by Yahoo Finance via yfinance | Built with Streamlit")