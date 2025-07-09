import pandas as pd

def load_miner_database():
    try:
        return pd.read_csv("data/miners.csv")
    except:
        return pd.DataFrame(columns=["model", "cost", "hashrate_ths", "power_kw"])