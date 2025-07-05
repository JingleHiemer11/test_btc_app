#Normalize data

import pandas as pd

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

    cols_to_clean = ['daily_profit', 'daily_revenue', 'cost']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].replace('[\$,]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    numeric_cols = ['power', 'hashrate', 'efficiency', 'noise_level']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if {'daily_profit', 'daily_revenue'}.issubset(df.columns):
        df['margin'] = (df['daily_profit'] / df['daily_revenue']) * 100
    if {'cost', 'efficiency'}.issubset(df.columns):
        df['cost_per_efficiency'] = df['cost'] / df['efficiency']

    return df
