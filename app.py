
import streamlit as st
import yfinance as yf
import feedparser
import pandas as pd
from urllib.parse import quote_plus
from datetime import datetime



import streamlit as st



# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="MarketPulse India",
    page_icon="📈",
    layout="wide"
)

st.title("📈 MarketPulse India")
st.caption("Simple Indian Stock Market Alert Dashboard")



# Increase font size
st.markdown("""
<style>
    /* Main text */
    html, body, [class*="css"] {
        font-size: 20px;
    }

    p {
        font-size: 20px;
    }

    /* Headings */
    h1 {
        font-size: 40px !important;
    }

    h2 {
        font-size: 32px !important;
    }

    h3 {
        font-size: 26px !important;
    }

    /* Sidebar width */
    section[data-testid="stSidebar"] {
        width: 500px !important;
        min-width: 450px !important;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] * {
        font-size: 26px;
    }

    /* Buttons */
    button {
        font-size: 26px !important;
    }
</style>
""", unsafe_allow_html=True)
# --------------------------------------------------
# STOCK LIST
# --------------------------------------------------

STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "ITC": "ITC.NS",
    "SBI": "SBIN.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Bharti Airtel": "BHARTIARTL.NS"
}

INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN"
}

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "alert_history" not in st.session_state:
    st.session_state.alert_history = []

if "reference_prices" not in st.session_state:
    st.session_state.reference_prices = {}

# --------------------------------------------------
# FUNCTIONS
# --------------------------------------------------

@st.cache_data(ttl=60)
def get_stock_data(symbol):

    try:
        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period="5d",
            interval="1d",
            auto_adjust=False
        )

        if data.empty:
            return None

        data = data.dropna(subset=["Close"])

        if data.empty:
            return None

        latest_close = float(data["Close"].iloc[-1])

        previous_close = None

        if len(data) >= 2:
            previous_close = float(data["Close"].iloc[-2])

        if previous_close and previous_close != 0:
            daily_change = (
                (latest_close - previous_close)
                / previous_close
            ) * 100
        else:
            daily_change = None

        return {
            "price": latest_close,
            "previous_close": previous_close,
            "change": daily_change,
            "date": data.index[-1].strftime("%Y-%m-%d")
        }

    except Exception as e:

        return {
            "error": str(e)
        }


def get_movement(reference_price, current_price):

    if reference_price <= 0:
        return 0

    return (
        (current_price - reference_price)
        / reference_price
    ) * 100


def check_alert(
    stock_name,
    current_price,
    threshold
):

    if stock_name not in st.session_state.reference_prices:

        st.session_state.reference_prices[stock_name] = current_price

        return None

    reference_price = st.session_state.reference_prices[stock_name]

    movement = get_movement(
        reference_price,
        current_price
    )

    if abs(movement) >= threshold:

        direction = "UP" if movement > 0 else "DOWN"

        alert = {
            "stock": stock_name,
            "direction": direction,
            "movement": round(movement, 2),
            "price": round(current_price, 2),
            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        return alert

    return None


def get_news(query="Indian stock market"):

    try:

        encoded_query = quote_plus(query)

        url = (
            "https://news.google.com/rss/search?"
            f"q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        )

        feed = feedparser.parse(url)

        news_list = []

        for item in feed.entries[:15]:

            news_list.append({
                "title": item.get("title", "No title"),
                "link": item.get("link", ""),
                "published": item.get(
                    "published",
                    "Time unavailable"
                )
            })

        return news_list

    except Exception as e:

        return []


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("⚙️ Settings")

selected_stock_names = st.sidebar.multiselect(
    "Select stocks to monitor",
    options=list(STOCKS.keys()),
    default=[
        "Reliance Industries",
        "TCS",
        "Infosys"
    ]
)

threshold = st.sidebar.slider(
    "Alert threshold (%)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.5
)

if st.sidebar.button("🔄 Refresh Data"):

    st.cache_data.clear()

    st.rerun()


# --------------------------------------------------
# MARKET OVERVIEW
# --------------------------------------------------

st.header("🇮🇳 Market Overview")

market_columns = st.columns(2)

for index, (name, symbol) in enumerate(INDICES.items()):

    result = get_stock_data(symbol)

    with market_columns[index]:

        st.subheader(name)

        if result is None or "error" in result:

            st.warning("Market data unavailable")

        else:

            st.metric(
                label="Latest Available Close",
                value=f"₹{result['price']:,.2f}",
                delta=(
                    f"{result['change']:.2f}%"
                    if result["change"] is not None
                    else "N/A"
                )
            )

            st.caption(
                f"Data date: {result['date']}"
            )


# --------------------------------------------------
# STOCK WATCHLIST
# --------------------------------------------------

st.header("📊 Your Watchlist")

if not selected_stock_names:

    st.info("Select at least one stock from the sidebar.")

else:

    for stock_name in selected_stock_names:

        symbol = STOCKS[stock_name]

        result = get_stock_data(symbol)

        with st.container(border=True):

            st.subheader(stock_name)

            if result is None or "error" in result:

                st.error("Unable to fetch stock data.")

                continue

            price = result["price"]
            change = result["change"]

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Latest Available Price",
                    f"₹{price:,.2f}"
                )

            with col2:

                st.metric(
                    "Daily Change",
                    (
                        f"{change:.2f}%"
                        if change is not None
                        else "N/A"
                    )
                )

            with col3:

                st.write("**Data Date**")
                st.write(result["date"])

            # ------------------------------
            # ALERT CHECK
            # ------------------------------

            alert = check_alert(
                stock_name,
                price,
                threshold
            )

            if alert:

                st.warning(
                    f"🔔 ALERT: {stock_name} "
                    f"moved {alert['movement']}% "
                    f"from your reference price."
                )

                if not any(
                    a["stock"] == alert["stock"]
                    and a["direction"] == alert["direction"]
                    and a["price"] == alert["price"]
                    for a in st.session_state.alert_history
                ):

                    st.session_state.alert_history.append(
                        alert
                    )


# --------------------------------------------------
# ALERT HISTORY
# --------------------------------------------------

st.header("🔔 Alert History")

if st.session_state.alert_history:

    alert_df = pd.DataFrame(
        st.session_state.alert_history
    )

    st.dataframe(
        alert_df,
        use_container_width=True,
        hide_index=True
    )

    if st.button("Clear Alert History"):

        st.session_state.alert_history = []

        st.rerun()

else:

    st.info(
        "No alerts yet. Refresh the app after "
        "a stock crosses your configured threshold."
    )


# --------------------------------------------------
# FINANCIAL NEWS
# --------------------------------------------------

st.header("📰 Financial News")

news_query = st.text_input(
    "Search financial news",
    value="Indian stock market"
)

if st.button("🔎 Fetch News"):

    with st.spinner("Fetching news..."):

        news = get_news(news_query)

    if news:

        for item in news:

            st.markdown(
                f"### [{item['title']}]({item['link']})"
            )

            st.caption(
                item["published"]
            )

            st.divider()

    else:

        st.warning(
            "No news found or the news service "
            "is currently unavailable."
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "MarketPulse India | Prototype"
)

st.caption(
    "Market data may be delayed or unavailable. "
    "This app is for informational and educational "
    "purposes only and is not investment advice."
)