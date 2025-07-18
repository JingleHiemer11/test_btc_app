#metrics.py

def calculate_profitability_metrics(
    df,
    btc_price=None,
    electricity_rate=0.05,
    difficulty=None,
    block_reward_btc=6.25,
    fees_btc=0.0,
    usd_per_th_per_day=None,
    uptime=0.95
):
    df = df.copy()

    if usd_per_th_per_day is not None:
        # Calculate revenue directly from hashprice
        df["daily_revenue"] = df["hashrate_ths"] * usd_per_th_per_day

        # Calculate electricity cost
        df["daily_electric_cost"] = df["power_kw"] * 24 * electricity_rate * uptime

        # Profit and break-even
        df["daily_profit"] = df["daily_revenue"] - df["daily_electric_cost"]
        df["break_even"] = df.apply(
            lambda row: (row["cost"] / row["daily_profit"] / 30) if row["daily_profit"] > 0 else None,
            axis=1
        )

    else:
        # Difficulty-based calculation fallback
        # Make sure 'daily_btc_mined' column exists in df when using this path
        df["daily_revenue"] = df["daily_btc_mined"] * btc_price
        df["daily_electric_cost"] = df["power_kw"] * 24 * electricity_rate * uptime
        df["daily_profit"] = df["daily_revenue"] - df["daily_electric_cost"]
        df["break_even"] = df.apply(
            lambda row: (row["cost"] / row["daily_profit"] / 30) if row["daily_profit"] > 0 else None,
            axis=1
        )

    # ---- Financial Metrics (applies to both cases) ----
    df["annual_profit"] = df["daily_profit"] * 365
    df["irr_1yr"] = (df["annual_profit"] - df["cost"]) / df["cost"]
    df["ppi_1yr"] = df["annual_profit"] / df["cost"]
    df["cpbm"] = df.apply(
        lambda row: (row["cost"] / row["daily_btc_mined"]) if "daily_btc_mined" in df.columns and row["daily_btc_mined"] > 0 else None,
        axis=1
    )

    return df