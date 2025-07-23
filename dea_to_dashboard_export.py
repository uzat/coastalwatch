import os
import json
import base64
import ee
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def initialize_earth_engine():
    b64 = os.environ.get("EARTHENGINE_SERVICE_ACCOUNT_JSON")
    if not b64:
        raise Exception("EARTHENGINE_SERVICE_ACCOUNT_JSON not found in environment variables.")
    try:
        decoded = base64.b64decode(b64).decode("utf-8")
        credentials_json = json.loads(decoded)
        credentials = ee.ServiceAccountCredentials(
            email=credentials_json["client_email"],
            key_data=json.dumps(credentials_json)
        )
        ee.Initialize(credentials)
        print("✅ Earth Engine initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Earth Engine: {e}")
        sys.exit(1)

def get_ndvi_timeseries(location):
    lon, lat = location["lon"], location["lat"]
    point = ee.Geometry.Point([lon, lat])
    start_date = "2022-01-01"
    end_date = "2023-12-31"

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start_date, end_date)
        .filterBounds(point)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(lambda img: img.addBands(
            img.normalizedDifference(["B8", "B4"]).rename("NDVI"))
                .copyProperties(img, ["system:time_start"])
        )
    )

    def extract_info(image):
        date = ee.Date(image.get("system:time_start")).format("YYYY-MM-dd")
        ndvi = image.select("NDVI").reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=10).get("NDVI")
        return ee.Feature(None, {"date": date, "ndvi": ndvi})

    features = collection.map(extract_info).filter(
        ee.Filter.notNull(["ndvi"])).aggregate_array("properties")

    return features.getInfo()

def save_ndvi_csv(location_name, ndvi_data):
    folder = f"data/NDVI/{location_name}"
    os.makedirs(folder, exist_ok=True)

    df = pd.DataFrame(ndvi_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values("date")
    csv_path = f"{folder}/ndvi.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved CSV: {csv_path}")
    return df

def export_ndvi_chart(location_name, df):
    folder = f"data/NDVI/{location_name}"
    os.makedirs(folder, exist_ok=True)

    try:
        plt.figure(figsize=(10, 5))
        plt.plot(df['date'], df['ndvi'], marker='o')
        plt.title(f"NDVI Time Series – {location_name.replace('_', ' ')}")
        plt.xlabel("Date")
        plt.ylabel("NDVI")
        plt.grid(True)
        plt.tight_layout()

        chart_path = f"{folder}/ndvi_chart.png"
        plt.savefig(chart_path)
        plt.close()
        print(f"✅ Saved chart: {chart_path}")
    except Exception as e:
        print(f"⚠️ Could not generate chart for {location_name}: {e}")

def main():
    initialize_earth_engine()

    locations = {
        "Rainbow_Beach": {"lat": -25.9028, "lon": 153.0956},
        "Byron_Bay": {"lat": -28.6474, "lon": 153.6020},
    }

    for name, loc in locations.items():
        print(f"📍 Processing location: {name}")
        try:
            ndvi_data = get_ndvi_timeseries(loc)
            df = save_ndvi_csv(name, ndvi_data)
            export_ndvi_chart(name, df)
        except Exception as e:
            print(f"❌ Failed to process {name}: {e}")

if __name__ == "__main__":
    main()
