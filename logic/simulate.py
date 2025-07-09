import pandas as pd

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
    btc_cagr: float
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

    results = []

    for year in range(1, years + 1):
        halvings_passed = (year - 1) // HALVING_INTERVAL
        reward = block_reward / (2 ** halvings_passed)

        share = hashrate_ths / network_hashrate_ths if network_hashrate_ths > 0 else 0.0
        btc_mined = share * BLOCKS_PER_DAY * reward * DAYS_PER_YEAR
        energy_cost = power_kw * 24 * 365 * electricity_rate

        btc_held += btc_mined
        btc_price *= (1 + btc_cagr / 100)
        btc_value = btc_held * btc_price
        roi = btc_value - initial_investment
        if scenario != "HODL":
            roi -= loan_amount

        results.append({
            "Year": year,
            "Scenario": scenario,
            "BTC Price": btc_price,
            "BTC Held": btc_held,
            "BTC Mined": btc_mined,
            "Energy Cost ($)": energy_cost,
            "BTC Value ($)": btc_value,
            "ROI ($)": roi
        })

        network_hashrate_ths *= NETWORK_GROWTH

    return results

def simulate_all_scenarios(user_inputs):
    scenarios = ["HODL", "Miners Only", "BTC Loan", "Hybrid"]
    all_results = []
    for scenario in scenarios:
        result = simulate_scenario(scenario=scenario, **user_inputs)
        all_results.extend(result)
    return pd.DataFrame(all_results)
