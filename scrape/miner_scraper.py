#Scrape live miner info from Internet

import requests
from bs4 import BeautifulSoup

def scrape_miner_specs(miner_name):
    base_url = "https://www.asicminervalue.com"
    search_url = f"{base_url}/search?q={miner_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        search_response = requests.get(search_url, headers=headers)
        search_soup = BeautifulSoup(search_response.text, "html.parser")
        link_tag = search_soup.select_one(".miner-list a")

        if not link_tag:
            return None

        miner_url = base_url + link_tag['href']
        detail_response = requests.get(miner_url, headers=headers)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        specs_table = detail_soup.select_one("table.specs")
        if not specs_table:
            return None

        specs = {}
        for row in specs_table.select("tr"):
            cols = row.select("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                specs[key] = value

        return {
            "Noise Level (dB)": specs.get("Noise level"),
            "Operating Temp (°C)": specs.get("Operating temperature"),
            "Length (mm)": specs.get("Size", "").split("x")[0].strip(),
            "Width (mm)": specs.get("Size", "").split("x")[1].strip() if "x" in specs.get("Size", "") else None,
            "Height (mm)": specs.get("Size", "").split("x")[2].strip() if "x" in specs.get("Size", "") else None,
            "Weight (kg)": specs.get("Weight"),
        }
    except Exception:
        return None
