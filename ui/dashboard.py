#dashboard.py

def run_dashboard():
    import datetime
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import streamlit as st
    import time
    import os
    import numpy as np

    from data.btc_api import fetch_btc_prices, fetch_hashprice
    from data.miner_data import load_data, update_csv
    from scrape.miner_scraper import scrape_miner_specs
    from ui.column_config import column_config
    from ui.column_config import scenario_column_config
    from utils.cleaning import clean_and_normalize
    from utils.scoring import calculate_miner_scores
    from utils.metrics import calculate_profitability_metrics
    from logic.inputs import get_user_inputs
    from logic.simulate import simulate_all_scenarios
    
    df = load_data()  # loads, cleans, renames, power → power_kw

    if df.empty:
        st.warning("No miner data loaded. Upload CSV or add miners manually.")

    def update_miner_revenue_profit(df, btc_price, electricity_rate, usd_per_th_per_day=None):
        df = df.copy()

        # If you have a live usd_per_th_per_day from hashprice API, use that,
        # else estimate it from btc_price and a rough factor.
        if usd_per_th_per_day is None:
            # Rough estimate: assume BTC mining yields ~0.06 USD per TH/s/day at btc_price=30k,
            # scale linearly with btc_price:
            base_btc_price = 100000
            base_usd_per_th_per_day = 0.06
            usd_per_th_per_day = base_usd_per_th_per_day * (btc_price / base_btc_price)

        st.write(f"BTC Price used: {btc_price}")
        st.write(f"USD per TH per day: {usd_per_th_per_day}")
        st.write(f"Sample miner hashrate (TH/s): {df['hashrate_ths'].iloc[0] if not df.empty else 'No data'}")


        # Calculate daily revenue ($)
        df["daily_revenue"] = df["hashrate_ths"] * usd_per_th_per_day

        # Calculate daily electricity cost ($)
        df["daily_cost"] = df["power_kw"] * 24 * electricity_rate

        # Calculate daily profit ($)
        df["daily_profit"] = df["daily_revenue"] - df["daily_cost"]

        # Profit margin (%)
        df["margin_percent"] = 100 * df["daily_profit"] / df["daily_revenue"].replace(0, 1)  # avoid div by zero
        return df
    
    st.title("Bitcoin Miner Scraper & Dashboard")

    # === Live Bitcoin Price Chart ===
    st.subheader("📈 Live Bitcoin Price Chart")

    days_options = [7, 30, 90, 180, 365]
    selected_days = st.radio("Select time range (days)", days_options, index=1, horizontal=True)

    prices = fetch_btc_prices(days=selected_days)
    if prices:
        df_prices = pd.DataFrame(prices, columns=["timestamp", "price"])
        df_prices["date"] = pd.to_datetime(df_prices["timestamp"], unit="ms")

        fig = px.line(df_prices, x="date", y="price", title="Bitcoin Price (USD)")
        fig.update_traces(line_color="#F2A900")  # Bitcoin brand orange
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Unable to fetch BTC price data currently.")

    # Upload CSV
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df = clean_and_normalize(pd.read_csv(uploaded_file))

    # Prepare df_miner_db for inputs and scenarios
    df_miner_db = df[["model", "cost", "hashrate_ths", "power_kw"]].dropna().copy()
    df_miner_db["model"] = df_miner_db["model"].str.strip().str.lower()
    df_miner_db.rename(columns={"hashrate": "hashrate_ths"}, inplace=True)
    #df_miner_db.drop(columns=["power"], inplace=True)
    
    # Fetch live price for sidebar if needed
    prices = fetch_btc_prices(days=1)
    if prices:
        live_btc_price = prices[-1][1]  # last price in data
    else:
        live_btc_price = None

    # Get user inputs with live BTC price
    user_inputs = get_user_inputs(df_miner_db, live_btc_price=live_btc_price)

    # Fetch live hashprice from Luxor API
    usd_per_th_per_day, sats_per_th_per_day = fetch_hashprice()

    st.sidebar.markdown("### Live Hashprice (from Luxor API)")
    if usd_per_th_per_day is not None:
        st.sidebar.markdown(f"💰 ${usd_per_th_per_day:.6f} per TH/s per day")
    else:
        st.sidebar.markdown("⚠️ Unable to fetch live hashprice")

    # Update miner data with fresh revenue & profit based on current btc price & electricity
    df = update_miner_revenue_profit(
        df,
        btc_price=user_inputs["btc_price"],
        electricity_rate=user_inputs["electricity_rate"],
        usd_per_th_per_day=usd_per_th_per_day  # from live hashprice API if available
    )

    df_scenarios = simulate_all_scenarios(user_inputs)
    df_scenarios["Scenarios"] = df_scenarios["Scenario"].str.strip().str.lower()
    # Rename miner columns for consistency in downstream calculations
    rename_map = {
        "miner_cost": "cost",
        "miner_power_kw": "power_kw",
        "miner_hashrate_ths": "hashrate_ths"
    }
    for old_col, new_col in rename_map.items():
        df_scenarios[new_col] = df_scenarios.get(old_col, np.nan)

    df_scenarios = calculate_profitability_metrics(
        df_scenarios,
        btc_price=user_inputs["btc_price"],
        electricity_rate=user_inputs["electricity_rate"],
        difficulty=user_inputs.get("difficulty"),
        block_reward_btc=user_inputs.get("block_reward_btc"),
        fees_btc=user_inputs.get("fees_btc"),
        usd_per_th_per_day=user_inputs.get("usd_per_th_per_day"),
    )

    # --- Miner Data Section (AFTER metrics update) ---
    st.subheader("📋 Current Miner Database (with dynamic profit & cost)")
    columns_to_hide = ["power_kw", "daily_electric_cost"]  # define here or earlier
    if not df.empty:
        df_display = df.drop(columns=[col for col in columns_to_hide if col in df.columns])
        st.dataframe(df_display, column_config=column_config, use_container_width=True)
    else:
        st.info("No miner data available. Upload CSV or add miners manually.")
    
    # --- Add Miner Manually ---
    st.markdown("Upload your miner CSV, scrape specs, or add miners manually.")
    st.subheader("➕ Add a Miner Manually")
    with st.form("add_miner_form"):
        model = st.text_input("Model")
        manufacturer = st.text_input("Manufacturer")
        hashrate_ths = st.number_input("Hashrate (TH/s)", step=0.1)
        power = st.number_input("Power (W)", step=1)
        release_year = st.number_input("Release Year", step=1, format="%d")
        submitted = st.form_submit_button("Add Miner")

        if submitted and model and manufacturer:
            new_data = {
                "Model": model,
                "Manufacturer": manufacturer,
                "Hashrate (TH/s)": hashrate_ths,
                "Power (W)": power,
                "Efficiency (J/TH)": round(power / hashrate_ths, 2) if hashrate_ths else None,
                "Release Year": release_year
            }
            msg = update_csv(new_data)
            st.success(msg)

    # --- Scrape Specs ---
    st.subheader("🧲 Enrich Miner Specs via Web Scraping")
    if st.button("Scrape Specs for All Models"):
        enriched_df = df.copy()
        for idx, row in enriched_df.iterrows():
            model = row.get("model") or row.get("Model") or row.get("Model Name")
            if not model or not isinstance(model, str) or model.strip() == "":
                continue
            st.write(f"Scraping: {model}...")
            scraped = scrape_miner_specs(model)
            if scraped:
                for key, val in scraped.items():
                    enriched_df.loc[idx, key] = val
            time.sleep(1)

        enriched_df.to_csv("Book123.csv", index=False)
        st.success("✅ Specs scraped and updated.")
        st.dataframe(enriched_df)

    # Save updated miner DB with dynamic revenue/profit to CSV
    if "daily_revenue" in df.columns and "daily_profit" in df.columns:
        df.to_csv("Book123.csv", index=False)
    
    # --- Export CSV ---
    st.subheader("⬇️ Download Updated Miner List")
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv_data, file_name="updated_miners.csv", mime="text/csv")

    # --- Miner Comparison Charts ---
    st.subheader("📊 Miner Comparison Charts")

    if not df.empty:
        st.markdown("**Hashrate (TH/s) vs Power Consumption**")
        if "release_date" in df.columns:
            df["release_year"] = pd.to_datetime(df["release_date"], format="%y-%b", errors="coerce").dt.year
        fig1 = px.scatter(df, x="power_kw", y="hashrate_ths", color="model", hover_data=["release_year"])
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("**Miner Efficiency (J/TH)**")
        fig2 = px.bar(df.sort_values("efficiency"), x="model", y="efficiency", color="model", text_auto=".2s")
        st.plotly_chart(fig2, use_container_width=True)

        df_filtered = df.dropna(subset=["daily_profit", "cost", "efficiency"])
        fig3 = px.scatter(
            df_filtered,
            x="efficiency",
            y="cost",
            color="model",
            hover_name="model",
            title="Efficiency vs Cost",
        )
        st.plotly_chart(fig3, use_container_width=True)

        df_filtered["daily_profit_size"] = df_filtered["daily_profit"].apply(lambda x: max(x, 0))

        fig4 = px.scatter(
            df_filtered,
            x="cost",
            y="daily_profit",
            size="daily_profit_size",
            color="model",
            hover_name="model",
            title="Cost vs Daily Profit",
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No miner data to chart yet. Add or upload miners first.")

    # === BTC Investment Scenario Simulator ===
    st.subheader("💡 BTC Investment Strategy Simulator")

    selected_strategies = st.multiselect(
        "Select strategy/scenarios to compare",
        options=df_scenarios["Scenario"].unique().tolist(),
        default=["HODL"],
        key="strategy_selector",
    )

    if not df_scenarios.empty and "Year" in df_scenarios.columns and selected_strategies:
        df_filtered = df_scenarios[df_scenarios["Scenario"].isin(selected_strategies)].copy()

        fig = px.line(
            df_filtered,
            x="Year",
            y=["ROI ($)"],
            color="Scenario",
            title="ROI Over Time by Strategy",
        )

        y_min = min(df_filtered["ROI ($)"].min(), 0)
        y_max = df_filtered["ROI ($)"].max() * 1.1  # Add padding to top

        fig.update_layout(
            yaxis=dict(range=[y_min, y_max]),
            xaxis_title="Year",
            yaxis_title="ROI ($)",
            title_font_size=20,
            margin=dict(l=40, r=40, t=60, b=40),
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_filtered, column_config=scenario_column_config, use_container_width=True)
    else:
        st.warning("⚠️ No scenario data to display or selected.")

    if df_scenarios.empty:
        st.warning("No scenario simulation results. Check inputs or try again.")
        return