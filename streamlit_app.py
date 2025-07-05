import streamlit as st
from ui.dashboard import run_dashboard

st.set_page_config(page_title="Bitcoin Miner Dashboard", layout="wide")

# Run the main dashboard
run_dashboard()


#import streamlit as st
#from data.fetch_data import fetch_btc_prices
#from components.btc_chart import plot_price_chart

#st.set_page_config(page_title="BTC Dashboard", layout="wide")
#st.title("📈 Bitcoin Price Dashboard")

# Time interval buttons
#st.subheader("Select Time Range")
#interval_options = [1, 7, 30, 90, 180, 365] #Removed "max"
#selected_days = st.radio(
#    label="",
#    options=interval_options,
#    index=2,
#    horizontal=True,
#    key="days_radio"
#)
#currency = "usd"

# Load data
#prices = fetch_btc_prices(currency, selected_days)

# Show chart
#plot_price_chart(prices, currency, selected_days)