
def run_dashboard():
    import datetime
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import streamlit as st
    import time

    from data.miner_data import load_data, update_csv
    from scrape.miner_scraper import scrape_miner_specs
    from utils.cleaning import clean_and_normalize
    from data.btc_api import fetch_btc_prices

    st.title("Bitcoin Miner Scraper & Dashboard")

    # === Live Bitcoin Price Chart ===
    st.subheader("📈 Live Bitcoin Price Chart")

    days_options = [7, 30, 90, 180, 365]
    selected_days = st.radio("Select time range (days)", days_options, index=1,horizontal=True)

    prices = fetch_btc_prices(days=selected_days)
    if prices:
        df_prices = pd.DataFrame(prices, columns=["timestamp", "price"])
        df_prices["date"] = pd.to_datetime(df_prices["timestamp"], unit="ms")

        fig = px.line(df_prices, x="date", y="price", title="Bitcoin Price (USD)")
        fig.update_traces(line_color="#F2A900")  # Bitcoin brand orange
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Unable to fetch BTC price data currently.")

    # --- Miner Data Section ---
    st.markdown("Upload your miner CSV, scrape specs, or add miners manually.")

    df = load_data()
    st.subheader("📄 Current Miner Database")
    st.dataframe(df)

    # Upload CSV
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

    # --- Add Miner Manually ---
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
            #st.write(f"Skipping empty or invalid model at row {idx}")
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
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv_data, file_name="updated_miners.csv", mime="text/csv")

    # --- Charts ---
    st.subheader("📊 Miner Comparison Charts")
    df = clean_and_normalize(df)

    if not df.empty:
        st.markdown("**Hashrate vs Power Consumption**")
        fig1 = px.scatter(df, x="power", y="hashrate", color="model", hover_data=["release_date"])
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("**Miner Efficiency (J/TH)**")
        fig2 = px.bar(df.sort_values("efficiency"), x="model", y="efficiency", color="model", text_auto=".2s")
        st.plotly_chart(fig2, use_container_width=True)

        df_filtered = df.dropna(subset=['daily_profit', 'cost', 'efficiency'])
        fig3 = px.scatter(df_filtered,
                         x='efficiency',
                         y='cost',
                         size='daily_profit',
                         color='margin',
                         hover_name='model',
                         title='Efficiency vs Cost vs Profit Margin')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No miner data to chart yet. Add or upload miners first.")