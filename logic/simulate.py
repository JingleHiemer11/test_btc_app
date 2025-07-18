#simulate.py

import pandas as pd
import numpy as np
import streamlit as st

def simulate_scenario(
    scenario: str,
    initial_investment: float,
    btc_price: float,
    electricity_rate: float,
    years: int,
    miner_cost: float,
    miner_hashrate_ths: float,
    miner_power_kw: float,
    network_hashrate_ehs: float,
    btc_cagr: float,
    start_year: int = 2026,
    difficulty: float = None,
    fees_btc: float = 0.025,
    uptime: float = 0.95,
    block_reward: float = 50.0
):
    BLOCKS_PER_DAY = 144
    DAYS_PER_YEAR = 365
    HALVING_INTERVAL = 4
    NETWORK_GROWTH = 1.10
    GENESIS_YEAR = 2009  # mining started in early 2009
    FIRST_HALVING_YEAR = 2012
    HALVING_INTERVAL = 4

    # Calculate initial halvings at start_year
    initial_halvings = max(0, (start_year - FIRST_HALVING_YEAR) // HALVING_INTERVAL)

    miner_count = 0
    btc_held = 0.0
    loan_amount = 0.0

    # Initial strategy logic
    if scenario == "HODL":
        btc_held = initial_investment / btc_price
        
    elif scenario == "Miners Only":
        miner_count = int(initial_investment / miner_cost)
        
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
        calendar_year = start_year + (year - 1)
        halvings_passed = max(0, (calendar_year - FIRST_HALVING_YEAR) // HALVING_INTERVAL)
        halving_diff = halvings_passed - initial_halvings
        reward = block_reward / (2 ** halving_diff) if halving_diff >= 0 else block_reward * (2 ** abs(halving_diff))


        if difficulty is not None and difficulty > 0:

            # Convert miner hashrate TH/s to H/s
            hashrate_hs = hashrate_ths * 1e12
            reward_per_block = reward + fees_btc
            daily_btc_mined = (hashrate_hs * uptime * reward_per_block * 86400) / (difficulty * 2**32)
            btc_mined = daily_btc_mined * DAYS_PER_YEAR

        else:
            share = hashrate_ths / network_hashrate_ths if network_hashrate_ths > 0 else 0.0
            btc_mined = share * BLOCKS_PER_DAY * reward * DAYS_PER_YEAR
            daily_btc_mined = btc_mined / 365
            
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
            "btc_mined": btc_mined,
            "daily_btc_mined": daily_btc_mined,
            "Energy Cost ($)": energy_cost,
            "ROI ($)": roi,
            "CAGR (%)": cagr,
            "Calendar Year": start_year + year - 1
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

def filter_simulate_inputs(user_inputs):
    # Helper to filter only needed keys for simulate_scenario
    allowed_keys = {
        "initial_investment",
        "btc_price",
        "electricity_rate",
        "years",
        "miner_cost",
        "miner_hashrate_ths",
        "miner_power_kw",
        "network_hashrate_ehs",
        "btc_cagr",
        "difficulty",
        "fees_btc",
        "start_year",
        "block_reward"
    }
    return {k: v for k, v in user_inputs.items() if k in allowed_keys}

def simulate_all_scenarios(user_inputs):
    scenarios = ["HODL", "Miners Only", "BTC Loan", "Hybrid"]
    filtered_inputs = filter_simulate_inputs(user_inputs)
    
    all_results = []
    for scenario in scenarios:
        # Pass scenario explicitly, other args unpacked from filtered inputs
        result = simulate_scenario(scenario=scenario, **filtered_inputs)
        all_results.extend(result)
    return pd.DataFrame(all_results)

def simulate_single_scenario(scenario, user_inputs):
    filtered_inputs = filter_simulate_inputs(user_inputs)
    return pd.DataFrame(simulate_scenario(scenario=scenario, **filtered_inputs))