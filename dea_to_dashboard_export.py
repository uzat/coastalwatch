import ee
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def initialize_earth_engine():
    service_account_json = os.getenv('EARTHENGINE_SERVICE_ACCOUNT_JSON')
    if not service_account_json:
        raise Exception("EARTHENGINE_SERVICE_ACCOUNT_JSON not found in environment variables.")

    credentials_dict = json.loads(service_account_json)
    credentials = ee.ServiceAccountCredentials(credentials_dict['client_email'], key_data=credentials_dict)
    ee.Initialize(credentials)

def export_ndvi_chart(location_name, ndvi_data):
    os.makedirs("output", exist_ok=True)

    try:
        df = pd.DataFrame(ndvi_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values("date")

        plt.figure(figsize=(10, 5))
        plt.plot(df['date'], df['ndvi'], marker='o')
        plt.title(f"NDVI Time Series – {location_name.replace('_', ' ')}")
        plt.xlabel("Date")
        plt.ylabel("NDVI")
        plt.grid(True)
        plt.tight_layout()

        chart_path = f"output/{location_name}_ndvi_chart.png"
        plt.savefig(chart_path)
        plt.close()
        print(f"✅ Saved chart for {location_name}: {chart_path}")
    except Exception as e:
        print(f"⚠️ Could not generate chart for {location_name}: {e}")

def main():
    initialize_earth_engine()

    locations = ["Rainbow_Beach", "Byron_Bay"]  # Add more as needed
    for location in locations:
        print(f"📍 Processing location: {location}")

        # Simulate NDVI data retrieval – replace this block with actual Earth Engine export
        # Your real NDVI data export function should return a list of dicts like:
        # [{"date": "2024-01-01", "ndvi": 0.67}, ...]
        dummy_data = [
            {"date": "2024-01-01", "ndvi": 0.55},
            {"date": "2024-02-01", "ndvi": 0.60},
            {"date": "2024-03-01", "ndvi": 0.62},
        ]

        export_ndvi_chart(location, dummy_data)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Failed to initialize Earth Engine: {e}")
