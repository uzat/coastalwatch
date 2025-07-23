import os
import json
import base64
import ee
import pandas as pd
import matplotlib.pyplot as plt
import sys


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


def fetch_ndvi_data(location_name, lon, lat):
    point = ee.Geometry.Point([lon, lat])
    collection = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(point) \
        .filterDate('2022-01-01', '2025-01-01') \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .map(lambda img: img.addBands(img.normalizedDifference(['B8', 'B4']).rename('NDVI')))

    def extract_feature(img):
        date = img.date().format("YYYY-MM-dd")
        ndvi = img.select('NDVI').reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10
        ).get('NDVI')
        return ee.Feature(None, {"date": date, "ndvi": ndvi})

    features = collection.map(extract_feature).filter(ee.Filter.notNull(["ndvi"]))

    try:
        dates = features.aggregate_array("date").getInfo()
        values = features.aggregate_array("ndvi").getInfo()
        return [{"date": d, "ndvi": v} for d, v in zip(dates, values) if v is not None]
    except Exception as e:
        print(f"⚠️ Failed to retrieve NDVI data for {location_name}: {e}")
        return []


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

    locations = {
        "Rainbow_Beach": (153.088, -25.903),
        "Byron_Bay": (153.6167, -28.6333),
    }

    for name, (lon, lat) in locations.items():
        print(f"📍 Processing location: {name}")
        try:
            ndvi_data = fetch_ndvi_data(name, lon, lat)
            if not ndvi_data:
                print(f"⚠️ No NDVI data for {name}")
                continue

            output_folder = f"data/NDVI/{name}"
            os.makedirs(output_folder, exist_ok=True)

            csv_path = f"{output_folder}/ndvi_summary_{name}.csv"
            pd.DataFrame(ndvi_data).to_csv(csv_path, index=False)
            print(f"✅ Saved NDVI CSV: {csv_path}")

            export_ndvi_chart(name, ndvi_data)

        except Exception as e:
            print(f"❌ Error processing {name}: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
