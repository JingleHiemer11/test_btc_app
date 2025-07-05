# Fetch API calls, CSV Loading, Etc

import requests
import streamlit as st

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

@st.cache_data(ttl=600)
def fetch_btc_prices(days: int = 30, currency: str = "usd"):
    """
    Fetch BTC price data from CoinGecko API for the last `days` days.
    """
    params = {
        "vs_currency": currency,
        "days": days,
        "interval": "daily"
    }
    try:
        response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["prices"]  # list of [timestamp, price]
    except Exception as e:
        st.error(f"Error fetching BTC prices: {e}")
        return []