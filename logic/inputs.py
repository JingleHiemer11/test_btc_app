import streamlit as st

def get_user_inputs(df_miners):
    # Miner selection
    miner_options = ["Manual Input"] + df_miners["model"].dropna().unique().tolist()
    selected_model = st.sidebar.selectbox("Choose Miner", miner_options)

    # BTC price
    btc_price_source = st.sidebar.radio("BTC Price Source:", ["Manual", "Live"])
    btc_price = st.sidebar.number_input("BTC Price (USD)", value=100_000.0)  # Stub for now

    initial_investment = st.sidebar.number_input("Initial Investment ($)", value=100_000.0)

    electricity_rate = st.sidebar.number_input("Electricity Rate ($/kWh)", value=0.01)
    years = st.sidebar.slider("Years to Simulate", 1, 40, 30)
    block_reward = st.sidebar.number_input("Current Block Reward", value=3.125)
    network_hashrate_ehs = st.sidebar.number_input("Network Hashrate (EH/s)", value=1000.0)
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
        "btc_price": btc_price,
        "initial_investment": initial_investment,
        "electricity_rate": electricity_rate,
        "years": years,
        "block_reward": block_reward,
        "network_hashrate_ehs": network_hashrate_ehs,
        "btc_cagr": btc_cagr,
        "miner_cost": miner_cost,
        "miner_hashrate_ths": miner_hashrate,
        "miner_power_kw": miner_power
    }