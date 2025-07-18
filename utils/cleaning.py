#cleaning.py

import pandas as pd
import numpy as np

def clean_and_normalize(df):
    if df.empty:
        return df

    df.columns = df.columns.str.strip().str.lower()

    df.rename(columns={
        "hashrate (th/s)": "hashrate",
        "watts": "power",
        "efficiency (j/th)": "efficiency",
        "noise level (db)": "noise_level",
        "model": "model",
        "manufacturer": "manufacturer",
        "release date": "release_date",
        "revenue (daily)": "daily_revenue",
        "profit (daily)": "daily_profit",
        "operating margin": "margin_percent",
        "cost per miner": "cost",
        "break-even (months)": "break_even"
    }, inplace=True)

    # Clean currency-formatted columns
    currency_cols = [
        'daily_profit', 'daily_revenue', 'cost',
        'cost_per_hash', 'expected_cost', 'excost_per_hash', 'price_diff_usd'
    ]
    for col in currency_cols:
        if col in df.columns:
            df[col] = df[col].replace('[\$,]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Clean percentage-formatted columns
    if "margin_percent" in df.columns:
        df["margin_percent"] = (
            df["margin_percent"].replace('%', '', regex=True).astype(float)
        )

    if "price_diff_usd" not in df.columns and "expected_cost" in df.columns:
        df["price_diff_usd"] = (df["expected_cost"] - df["cost"])

    if "price_diff_pct" not in df.columns and "expected_cost" in df.columns:
        df["price_diff_pct"] = ((df["expected_cost"]) / df["cost"].replace(0, np.nan)) * 100
        df["price_diff_pct"] = df["price_diff_pct"].fillna(0)  # Avoid NaN if cost was zero
    
    # Clean directly numeric columns
    numeric_cols = ['power', 'hashrate', 'efficiency', 'noise_level', 'break_even']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df