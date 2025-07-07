#Scoring file to provide math logic to rank miners in dashboard

from sklearn.preprocessing import MinMaxScaler
import pandas as pd

def calculate_miner_scores(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    df = df.copy()

    # Ensure required columns exist
    required_cols = ["efficiency", "daily_profit", "cost"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column: {col}")

    # Clean and convert columns first
    df["daily_profit"] = pd.to_numeric(df["daily_profit"], errors="coerce")
    df["daily_revenue"] = pd.to_numeric(df["daily_revenue"], errors="coerce")

    # Calculate margin if missing and daily_revenue exists
    if "margin" not in df.columns:
        if "daily_revenue" in df.columns:
            df["margin"] = (df["daily_profit"] / df["daily_revenue"]) * 100
        else:
            raise KeyError("Missing required column: 'margin' or 'daily_revenue' to calculate margin")

    # Drop rows missing any of these metrics
    df = df.dropna(subset=["efficiency", "daily_profit", "cost", "margin"]).copy()
    
    # Stop early if no data left
    if df.empty:
        return pd.DataFrame(columns=df.columns.tolist() + ["overall_score", "rank"])
    
    # Normalize numeric metrics
    scaler = MinMaxScaler()
    df[["eff_norm", "profit_norm", "cost_norm", "margin_norm"]] = scaler.fit_transform(
        df[["efficiency", "daily_profit", "cost", "margin"]]
    )

    # Invert where lower is better
    df["eff_score"] = 1 - df["eff_norm"]
    df["cost_score"] = 1 - df["cost_norm"]
    df["profit_score"] = df["profit_norm"]
    df["margin_score"] = df["margin_norm"]

    # Optional: use release year to estimate miner age
    if "release year" in df.columns:
        current_year = pd.Timestamp.now().year
        df["age"] = current_year - df["release year"]
        df["age_score"] = 1 - MinMaxScaler().fit_transform(df[["age"]])
    else:
        df["age_score"] = 0

    # Composite score
    df["overall_score"] = (
        weights["eff_score"] * df["eff_score"] +
        weights["cost_score"] * df["cost_score"] +
        weights["profit_score"] * df["profit_score"] +
        weights["margin_score"] * df["margin_score"] +
        weights["age_score"] * df["age_score"]
    )

    df["rank"] = df["overall_score"].rank(ascending=False)
    return df.sort_values("overall_score", ascending=False)