import ee
import os
import pandas as pd
import matplotlib.pyplot as plt

def export_ndvi_chart(csv_path: str, output_path: str):
    try:
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')

        plt.figure(figsize=(10, 5))
        plt.plot(df['Date'], df['NDVI'], marker='o', linestyle='-', color='green')
        plt.title('NDVI over Time')
        plt.xlabel('Date')
        plt.ylabel('NDVI')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        print(f"✅ Saved NDVI chart to {output_path}")
    except Exception as e:
        print(f"⚠️ Could not generate chart: {e}")

def process_location(location_name):
    ndvi_csv = f'data/NDVI/{location_name}/NDVI_{location_name}.csv'
    chart_path = f'data/NDVI/{location_name}/NDVI_{location_name}_chart.png'
    export_ndvi_chart(ndvi_csv, chart_path)

def initialize_earth_engine():
    try:
        ee.Initialize()
        print("✅ Earth Engine initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Earth Engine: {e}")
        raise

def main():
    locations = ["Rainbow_Beach", "Byron_Bay"]
    initialize_earth_engine()

    for loc in locations:
        print(f"📍 Processing location: {loc}")
        process_location(loc)

if __name__ == "__main__":
    main()