#miner_data.py
#Manually upload miner data from CSV file

import os
import pandas as pd
from utils.cleaning import clean_and_normalize

CSV_FILE = "Book123.csv"

# --- Load CSV ---
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df = clean_and_normalize(df)
        # Normalize for app usage
        if "hashrate" in df.columns:
            df.rename(columns={"hashrate": "hashrate_ths"}, inplace=True)

        if "power" in df.columns:
            df["power_kw"] = df["power"] / 1000  # Convert W ➝ kW
            df.drop(columns=["power"], inplace=True)
        return df
    else:
        return pd.DataFrame(columns=[
            "Model", "Manufacturer", "Hashrate (TH/s)", "Power (W)", "Efficiency (J/TH)",
            "Release Year", "Noise Level (dB)", "Operating Temp (°C)", 
            "Length (mm)", "Width (mm)", "Height (mm)", "Weight (kg)"
        ])

# --- Update CSV with new miner if not duplicate ---
def update_csv(new_data: dict):
    # Load existing data in original format
    df = pd.read_csv(CSV_FILE) if os.path.exists(CSV_FILE) else pd.DataFrame()

    # Map normalized keys back to original CSV column names
    reverse_rename_map = {
        "model": "Model",
        "manufacturer": "Manufacturer",
        "hashrate_ths": "Hashrate (TH/s)",
        "power_kw": "Power (W)",
        "efficiency": "Efficiency (J/TH)",
        "release_year": "Release Year",
        "noise_level": "Noise Level (dB)",
        # Add other mappings as needed
    }

    # Create a new dict with original keys
    new_data_original_keys = {}
    for k, v in new_data.items():
        new_key = reverse_rename_map.get(k.lower(), k)  # fallback to original key if no mapping
        # Convert power_kw (kW) back to Power (W)
        if new_key == "Power (W)" and v is not None:
            v = v * 1000  # kW to W
        new_data_original_keys[new_key] = v

    # If CSV is empty, create with columns from new_data keys
    if df.empty:
        df = pd.DataFrame(columns=new_data_original_keys.keys())

    # Check for duplicates by Model and Manufacturer (case insensitive)
    if not ((df["Model"].str.lower() == new_data_original_keys["Model"].lower()) & 
            (df["Manufacturer"].str.lower() == new_data_original_keys["Manufacturer"].lower())).any():
        df = pd.concat([df, pd.DataFrame([new_data_original_keys])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        return "✅ Added new miner to CSV."
    else:
        return "⚠️ Miner already exists in CSV."