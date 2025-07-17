import streamlit as st

column_config = {
    "model": st.column_config.TextColumn("Model"),
    "release_date": st.column_config.TextColumn("Release Date"),
    
    # Performance
    "hashrate": st.column_config.NumberColumn("Hashrate (TH/s)", format="%.2f"),
    "power": st.column_config.NumberColumn("Power (W)", format="%.0f"),
    "efficiency": st.column_config.NumberColumn("Efficiency (J/TH)", format="%.2f"),
    #"noise_level": st.column_config.NumberColumn("Noise (dB)", format="%.0f"),

    # Financials
    "daily_revenue": st.column_config.NumberColumn("Daily Revenue", format="$%.2f"),
    "daily_profit": st.column_config.NumberColumn("Daily Profit", format="$%.2f"),
    "margin_percent": st.column_config.NumberColumn("Margin (%)", format="%.1f%%"),
    "cost": st.column_config.NumberColumn("Cost", format="$%.2f"),
    "break_even": st.column_config.NumberColumn("Break-even (Months)", format="%.2f"),

    # Custom Calculated
    "cost_per_hash": st.column_config.NumberColumn("Cost/Hash ($/TH)", format="$%.2f"),
    "expected_cost": st.column_config.NumberColumn("Expected Cost", format="$%.2f"),
    "excost_per_hash": st.column_config.NumberColumn("Expected Cost/Hash", format="$%.2f"),
    "price_diff_usd": st.column_config.NumberColumn("Price Diff (USD)", format="$%.2f"),
    "price_diff_pct": st.column_config.NumberColumn("Price Diff (%)", format="%.1f%%"),
    "btc_mined": st.column_config.NumberColumn("BTC Mined (Daily)", format="%.8f"),

        # ✅ New Financial Metrics
    "annual_profit": st.column_config.NumberColumn("Annual Profit", format="$%.2f"),
    "irr_1yr": st.column_config.NumberColumn("IRR (1yr)", format="%.2f%%"),
    "ppi_1yr": st.column_config.NumberColumn("PPI (1yr)", format="%.2f"),
    "cpbm": st.column_config.NumberColumn("CPBM", format="$%.2f"),

    # Optional future metrics
    #"roi_speed_daily_pct": st.column_config.NumberColumn("ROI/Day", format="%.2f%%"),
    #"ppi_2yr": st.column_config.NumberColumn("PPI (2yr)", format="$%.0f"),
    #"cpbm_capex": st.column_config.NumberColumn("CPBM (Capex)", format="$%.0f"),
    #"cpbm_allin": st.column_config.NumberColumn("CPBM (All-in)", format="$%.0f"),
    #"btc_mined_2yr": st.column_config.NumberColumn("BTC Mined (2yr)", format="%.5f"),
}

scenario_column_config = {
    "IRR (%)": st.column_config.NumberColumn("IRR (%)", format="%.2f%%"),
    "CPBM (Months)": st.column_config.NumberColumn("Capex Payback (Months)", format="%.0f"),
    "PPI": st.column_config.NumberColumn("PPI", format="%.2f"),
    "Annual Profit": st.column_config.NumberColumn("Annual Profit", format="$%.2f"),
}