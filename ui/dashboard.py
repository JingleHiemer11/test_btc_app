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
    from logic.inputs import get_user_inputs
    from logic.simulate import simulate_all_scenarios

    csv_path = "Book123.csv"
    
    if os.path.exists(csv_path):
        df = clean_and_normalize(pd.read_csv(csv_path))
        # Safely convert power from watts to kilowatts if available
        if "power" in df.columns:
            df["power_kw"] = df["power"] / 1000
        else:
            st.warning("⚠️ 'power' column not found. Using default power input if provided.")
            df["power_kw"] = np.nan  # or a default like 3.4 if you want
    else:
        df = pd.DataFrame()  # empty df fallback

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
    df_miner_db = df[["model", "cost", "hashrate", "power"]].dropna().copy()
    df_miner_db["power_kw"] = df_miner_db["power"] / 1000  # watts to kilowatts
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

    # Calculate dynamic metrics based on availability of hashprice
    if usd_per_th_per_day is not None:
        # Calculate revenue directly from hashprice
        df["daily_revenue"] = df["hashrate"] * usd_per_th_per_day

        # Calculate electricity cost
        if "power" in df.columns:
            df["power_kw"] = df["power"] / 1000
        else:
            df["power_kw"] = np.nan  # or a default like 3.4
        df["daily_electric_cost"] = df["power_kw"] * 24 * user_inputs["electricity_rate"] * 0.95

        # Profit and break-even
        df["daily_profit"] = df["daily_revenue"] - df["daily_electric_cost"]
        df["break_even"] = df.apply(
            lambda row: (row["cost"] / row["daily_profit"] / 30) if row["daily_profit"] > 0 else None,
            axis=1
        )
    else:
        # Fallback to difficulty-based calculation
        def calculate_dynamic_metrics(df, btc_price, electricity_rate, difficulty, block_reward_btc, fees_btc, uptime=0.95):
            print("DEBUG: df.columns = ", df.columns.tolist())
            df = df.copy()
            if "power" in df.columns and "power_kw" not in df.columns:
                df["power_kw"] = df["power"] / 1000

            df["daily_revenue"] = df["daily_btc_mined"] * btc_price
            df["daily_electric_cost"] = df["power_kw"] * 24 * electricity_rate * uptime
            df["daily_profit"] = df["daily_revenue"] - df["daily_electric_cost"]
            df["break_even"] = df.apply(
                lambda row: (row["cost"] / row["daily_profit"] / 30) if row["daily_profit"] > 0 else None,
                axis=1
            )
            
            # ---- Financial Metrics ----
            df["annual_profit"] = df["daily_profit"] * 365
            df["irr_1yr"] = (df["annual_profit"] - df["cost"]) / df["cost"]
            df["ppi_1yr"] = df["annual_profit"] / df["cost"]
            df["cpbm"] = df.apply(
                lambda row: (row["cost"] / (row["daily_btc_mined"])) if row["daily_btc_mined"] > 0 else None,
                axis=1
            )

            return df

        df_scenarios = simulate_all_scenarios(user_inputs)
        st.write("DEBUG: df_scenarios columns:", df_scenarios.columns.tolist())
        # Standardize model column casing for safe merge
        df_scenarios["Scenarios"] = df_scenarios["Scenario"].str.strip().str.lower()
        df_miner_db["model"] = df_miner_db["model"].str.strip().str.lower()

        # Add 'power' from df_miner_db based on the selected miner model
        if "model" in df_scenarios.columns and "model" in df_miner_db.columns:
            df_scenarios = pd.merge(
                df_scenarios,
                df_miner_db[["model", "power", "power_kw", "cost"]],
                on="model",
                how="left"
            )
        else:
            st.warning("⚠️ Could not merge power data into scenario simulations.")

        df_scenarios = calculate_dynamic_metrics(
            df_scenarios,
            btc_price=user_inputs["btc_price"],
            electricity_rate=user_inputs["electricity_rate"],
            difficulty=user_inputs["difficulty"],
            block_reward_btc=user_inputs["block_reward"],
            fees_btc=user_inputs["fees_btc"],
            uptime=0.95
        )

    # --- Miner Data Section (AFTER metrics update) ---
    st.subheader("📋 Current Miner Database (with dynamic profit & cost)")

    if not df.empty:
        columns_to_hide = ["power_kw", "daily_electric_cost"]
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
        hashrate = st.number_input("Hashrate (TH/s)", step=0.1)
        power = st.number_input("Power (W)", step=1)
        release_year = st.number_input("Release Year", step=1, format="%d")
        submitted = st.form_submit_button("Add Miner")

        if submitted and model and manufacturer:
            new_data = {
                "Model": model,
                "Manufacturer": manufacturer,
                "Hashrate (TH/s)": hashrate,
                "Power (W)": power,
                "Efficiency (J/TH)": round(power / hashrate, 2) if hashrate else None,
                "Release Year": release_year
            }
            msg = update_csv(new_data)
            st.success(msg)

    # --- Scrape Specs ---
    st.subheader("🧲 Enrich Miner Specs via Web Scraping")
    if st.button("Scrape Specs for All Models"):
        enriched_df = df.copy()
        for idx, row in enriched_df.iterrows():
            model = row.get("Model") or row.get("Model Name")
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

    # --- Export CSV ---
    st.subheader("⬇️ Download Updated Miner List")
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv_data, file_name="updated_miners.csv", mime="text/csv")

    # --- Miner Comparison Charts ---
    st.subheader("📊 Miner Comparison Charts")

    if not df.empty:
        st.markdown("**Hashrate vs Power Consumption**")
        fig1 = px.scatter(df, x="power", y="hashrate", color="model", hover_data=["release_date"])
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

    if not df.empty:
        df_miner_db = df[["model", "cost", "hashrate", "power"]].dropna().copy()
        df_miner_db["power_kw"] = df_miner_db["power"] / 1000  # Convert Watts to kW
        df_miner_db.rename(columns={"hashrate": "hashrate_ths"}, inplace=True)
        df_miner_db.drop(columns=["power"], inplace=True)
    else:
        st.warning("⚠️ No valid miner data available. Please upload or enter at least one miner to continue.")
        return
    
    df_scenarios = simulate_all_scenarios(user_inputs)

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