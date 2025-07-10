# Fetch API calls, CSV Loading, Etc

import requests
import streamlit as st

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
HASHPRICE_API_URL = "https://api.hashrateindex.com/v1/hashrateindex/hashprice"

@st.cache_data(ttl=600)
def fetch_btc_prices(days: int = 30, currency: str = "usd") -> list:
    """
    Fetch BTC price data from CoinGecko API for the last `days` days.
    Returns a list of [timestamp, price].
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
        return data.get("prices", [])
    except Exception as e:
        st.error(f"Error fetching BTC prices: {e}")
        return []

@st.cache_data(ttl=600)
def fetch_hashprice() -> tuple[float | None, int | None]:
    headers = {
        "X-Hi-Api-Key": ""
    }
    params = {
        "currency": "USD",
        "hashunit": "THS",
        "bucket": "5m",
        "span": "1D"
    }
    """
    Fetch current Bitcoin hashprice from Luxor API.
    Returns (usd_per_th_per_day, sats_per_th_per_day).
    """
    try:
        resp = requests.get(HASHPRICE_API_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        usd_per_th_per_day = data["hashprice"]["usd_per_th_per_day"]
        sats_per_th_per_day = data["hashprice"]["sats_per_th_per_day"]
        return usd_per_th_per_day, sats_per_th_per_day
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            st.warning("⚠️ Access denied (403) to live hashprice API. Using manual difficulty input instead.")
        else:
            st.error(f"HTTP error fetching hashprice: {e}")
        return None, None
    except Exception as e:
        st.error(f"Error fetching hashprice: {e}")
        return None, None