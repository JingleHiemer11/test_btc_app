# utils/scoring.py

from sklearn.preprocessing import MinMaxScaler
import pandas as pd

def calculate_miner_scores(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    df = df.copy()

    # Ensure required columns exist
    required_cols = ["efficiency", "daily_profit", "cost"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column: {col}")

    df["daily_profit"] = pd.to_numeric(df["daily_profit"], errors="coerce")
    df["daily_revenue"] = pd.to_numeric(df["daily_revenue"], errors="coerce")

    if "margin" not in df.columns and "daily_revenue" in df.columns:
        df["margin"] = (df["daily_profit"] / df["daily_revenue"]) * 100

    if "price_diff_pct" not in df.columns and "expected_cost" in df.columns:
        df["price_diff_pct"] = (df["expected_cost"] / df["cost"]) * 100

    df = df.dropna(subset=["efficiency", "daily_profit", "cost", "margin"]).copy()

    if df.empty:
        return pd.DataFrame(columns=df.columns.tolist() + ["overall_score", "rank"])

    scaler = MinMaxScaler()
    df[["eff_norm", "profit_norm", "cost_norm", "margin_norm"]] = scaler.fit_transform(
        df[["efficiency", "daily_profit", "cost", "margin"]]
    )

    df["eff_score"] = 1 - df["eff_norm"]
    df["cost_score"] = 1 - df["cost_norm"]
    df["profit_score"] = df["profit_norm"]
    df["margin_score"] = df["margin_norm"]

    if "release year" in df.columns:
        current_year = pd.Timestamp.now().year
        df["age"] = current_year - df["release year"]
        df["age_score"] = 1 - MinMaxScaler().fit_transform(df[["age"]])
    else:
        df["age_score"] = 0

    df["overall_score"] = (
        weights["eff_score"] * df["eff_score"] +
        weights["cost_score"] * df["cost_score"] +
        weights["profit_score"] * df["profit_score"] +
        weights["margin_score"] * df["margin_score"] +
        weights["age_score"] * df["age_score"]
    )

    df["rank"] = df["overall_score"].rank(ascending=False)
    return df.sort_values("overall_score", ascending=False)