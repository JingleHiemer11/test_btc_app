#inputs.py

from typing import Optional, Dict, Any
import streamlit as st
import pandas as pd
import datetime

for key in st.session_state.keys():
    del st.session_state[key]

def get_user_inputs(df_miners: pd.DataFrame, live_btc_price: Optional[float] = None) -> Dict[str, Any]:
    # Miner selection
    miner_options = ["Manual Input"] + df_miners["model"].dropna().unique().tolist()
    selected_model = st.sidebar.selectbox("Choose Miner", miner_options)

    # BTC price
    btc_price_source = st.sidebar.radio("BTC Price Source:", ["Manual", "Live"])
    hashrate_mode = st.sidebar.radio("Hashrate Source", ["Manual (Difficulty)", "Live (API)"])

    # Show BTC price input only if Manual selected
    if btc_price_source == "Manual":
        btc_price = st.sidebar.number_input("BTC Price (USD)", value=100_000.0, step=5000.0, format="%.2f")
    else:
        btc_price = live_btc_price
        st.sidebar.markdown(f"**Live BTC Price:** ${btc_price:,.2f}" if btc_price else "*Fetching live price...*")

    # Show Difficulty input only if Manual selected
    if hashrate_mode == "Manual (Difficulty)":
        difficulty_t = st.sidebar.number_input("Network Difficulty (T)", value=115.00, step=1.00)
        difficulty = difficulty_t * 1e12
    else:
        difficulty = None  # Placeholder until API connected
        st.sidebar.markdown(f"**Live Difficulty:** *(Not available — API not connected)*")

    # Simulation Parameters
    initial_investment = st.sidebar.number_input("Initial Investment ($)", value=100_000.0, step=100_000.0)
    electricity_rate = st.sidebar.number_input("Electricity Rate ($/kWh)", value=0.01, step=0.01)
    years = st.sidebar.slider("Years to Simulate", 1, 40, 30)
    
    # Start year & dynamic block reward
    current_year = datetime.datetime.now().year
    start_year = st.sidebar.slider("Scenario Start Year", min_value=2009, max_value=2140, value=current_year + 1)
    halvings_passed = max(0, (start_year - 2009) // 4)
    block_reward = 50 / (2 ** halvings_passed)
    st.sidebar.markdown(f"📉 **Block Reward in {start_year}: {block_reward:.8f} BTC**")
    
    network_hashrate_ehs = st.sidebar.number_input("Network Hashrate (EH/s)", value=1000.0)
    fees_btc = st.sidebar.number_input("Daily Network Fees (BTC)", value=0.025, step=0.001, format="%.3f", key="fees_btc")
    btc_cagr = st.sidebar.number_input("BTC CAGR (%)", value=15.0)


    if selected_model == "Manual Input":
        miner_cost = st.sidebar.number_input("Miner Cost ($)", value=1000.0)
        miner_hashrate = st.sidebar.number_input("Miner Hashrate (TH/s)", value=100.0)
        miner_power = st.sidebar.number_input("Miner Power (kW)", value=3.0)
    else:
        row = df_miners[df_miners["model"] == selected_model].iloc[0]
        miner_cost = row["cost"]
        miner_hashrate = row["hashrate_ths"]
        miner_power = row["power_kw"]
        st.sidebar.markdown(f"**Specs:** {miner_hashrate} TH/s @ {miner_power} kW, ${miner_cost:,.0f}")

    return {
        "btc_price_source": btc_price_source,
        "btc_price": btc_price,
        "initial_investment": initial_investment,
        "electricity_rate": electricity_rate,
        "years": years,
        "start_year": start_year,
        "block_reward": block_reward,
        "network_hashrate_ehs": network_hashrate_ehs,
        "difficulty": difficulty,
        "fees_btc": fees_btc,
        "btc_cagr": btc_cagr,
        "miner_cost": miner_cost,
        "miner_hashrate_ths": miner_hashrate,
        "miner_power_kw": miner_power,
    }