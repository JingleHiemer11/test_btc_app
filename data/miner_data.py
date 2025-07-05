#Manually upload miner data from CSV file

import os
import pandas as pd

CSV_FILE = "Book123.csv"

# --- Load CSV ---
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        return pd.DataFrame(columns=[
            "Model", "Manufacturer", "Hashrate (TH/s)", "Power (W)", "Efficiency (J/TH)",
            "Release Year", "Noise Level (dB)", "Operating Temp (°C)", 
            "Length (mm)", "Width (mm)", "Height (mm)", "Weight (kg)"
        ])

# --- Update CSV with new miner if not duplicate ---
def update_csv(new_data: dict):
    df = load_data()

    if not ((df['Model'] == new_data['Model']) & (df['Manufacturer'] == new_data['Manufacturer'])).any():
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        return "✅ Added new miner to CSV."
    else:
        return "⚠️ Miner already exists in CSV."
