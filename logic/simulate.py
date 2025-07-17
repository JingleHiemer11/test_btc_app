import pandas as pd
import numpy as np
import streamlit as st

def simulate_scenario(
    scenario: str,
    initial_investment: float,
    btc_price: float,
    electricity_rate: float,
    years: int,
    block_reward: float,
    miner_cost: float,
    miner_hashrate_ths: float,
    miner_power_kw: float,
    network_hashrate_ehs: float,
    btc_cagr: float,
    difficulty: float = None,
    fees_btc: float = 0.025,
    uptime: float = 0.95
):
    BLOCKS_PER_DAY = 144
    DAYS_PER_YEAR = 365
    HALVING_INTERVAL = 4
    NETWORK_GROWTH = 1.10

    miner_count = 0
    btc_held = 0.0
    loan_amount = 0.0

    # Initial strategy logic
    if scenario == "HODL":
        btc_held = initial_investment / btc_price
    elif scenario == "Miners Only":
        miner_count = int(initial_investment / miner_cost)
        st.write(f"⚡ Miner Power Input (kW): {miner_power_kw}, Count: {miner_count}")
    elif scenario == "BTC Loan":
        btc_held = initial_investment / btc_price
        loan_amount = 0.10 * initial_investment
        miner_count = int(loan_amount / miner_cost)
    elif scenario == "Hybrid":
        half = initial_investment / 2
        btc_held = half / btc_price
        loan_amount = 0.10 * half
        miner_count = int((half + loan_amount) / miner_cost)

    hashrate_ths = miner_count * miner_hashrate_ths
    power_kw = miner_count * miner_power_kw
    network_hashrate_ths = network_hashrate_ehs * 1_000_000
    cumulative_energy_cost = 0.0  # Track total electricity cost over all years

    results = []
    yearly_profits = []

    for year in range(1, years + 1):
        halvings_passed = (year - 1) // HALVING_INTERVAL
        reward = block_reward / (2 ** halvings_passed)

        if difficulty is not None and difficulty > 0:
            # Convert miner hashrate TH/s to H/s
            hashrate_hs = hashrate_ths * 1e12
            reward_per_block = reward + (fees_btc / BLOCKS_PER_DAY)
            daily_btc_mined = (hashrate_hs * uptime * reward_per_block * BLOCKS_PER_DAY) / (difficulty * 2**32)
            btc_mined = daily_btc_mined * DAYS_PER_YEAR
        else:
            share = hashrate_ths / network_hashrate_ths if network_hashrate_ths > 0 else 0.0
            btc_mined = share * BLOCKS_PER_DAY * reward * DAYS_PER_YEAR

        energy_cost = power_kw * 24 * 365 * electricity_rate * uptime
        cumulative_energy_cost += energy_cost

        btc_held += btc_mined
        btc_price *= (1 + btc_cagr / 100)

        value_of_holdings = btc_held * btc_price
        roi = value_of_holdings - initial_investment - cumulative_energy_cost
        if scenario != "HODL":
            roi -= loan_amount

        yearly_cashflow = value_of_holdings - initial_investment - cumulative_energy_cost - loan_amount
        yearly_profits.append(yearly_cashflow)

        network_hashrate_ths *= NETWORK_GROWTH

        try:
            cagr = ((value_of_holdings / initial_investment) ** (1 / year) - 1) * 100
        except:
            cagr = None

        results.append({
            "Year": year,
            "Scenario": scenario,
            "BTC Price": btc_price,
            "BTC Held": btc_held,
            "BTC Mined": btc_mined,
            "Energy Cost ($)": energy_cost,
            "ROI ($)": roi,
            "CAGR (%)": cagr
        })

    # After yearly results, calculate long-term metrics:
    try:
        irr = np.irr([-initial_investment] + yearly_profits) * 100
    except:
        irr = None

    try:
        cumulative_cash = np.cumsum([0] + yearly_profits)
        breakeven_index = next(i for i, v in enumerate(cumulative_cash) if v >= initial_investment)
        months_to_breakeven = breakeven_index * 12
    except StopIteration:
        months_to_breakeven = None  # or some large number or string 'Never'

    total_profit = sum(yearly_profits)
    ppi = total_profit / initial_investment if initial_investment > 0 else None
    annual_profit = total_profit / years

    for r in results:
        if scenario != "HODL":
            r["IRR (%)"] = irr
            r["CPBM (Months)"] = months_to_breakeven
            r["PPI"] = ppi
            r["Annual Profit"] = annual_profit
        else:
            r["IRR (%)"] = None
            r["CPBM (Months)"] = None
            r["PPI"] = None
            r["Annual Profit"] = None

    return results

def simulate_all_scenarios(user_inputs):
    scenarios = ["HODL", "Miners Only", "BTC Loan", "Hybrid"]
    
    allowed_keys = {
        "initial_investment",
        "btc_price",
        "electricity_rate",
        "years",
        "block_reward",
        "miner_cost",
        "miner_hashrate_ths",
        "miner_power_kw",
        "network_hashrate_ehs",
        "btc_cagr",
        "difficulty",
        "fees_btc"
    }
    
    filtered_inputs = {k: v for k, v in user_inputs.items() if k in allowed_keys}
    
    all_results = []
    for scenario in scenarios:
        result = simulate_scenario(scenario=scenario, **filtered_inputs)
        all_results.extend(result)
    return pd.DataFrame(all_results)
