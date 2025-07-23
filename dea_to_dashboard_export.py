import os
import json
import base64
import ee
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
        raise


def get_ndvi_summary(location_geometry):
    start_date = "2024-01-01"
    end_date = datetime.today().strftime('%Y-%m-%d')

    try:
        s2 = ee.ImageCollection("COPERNICUS/S2_SR") \
            .filterBounds(location_geometry) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .map(lambda img: img
                 .normalizedDifference(['B8', 'B4'])
                 .rename('NDVI')
                 .set('date', img.date().format('YYYY-MM-dd')))

        features = s2.map(lambda img: ee.Feature(None, {
            'date': img.get('date'),
            'ndvi': img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=location_geometry,
                scale=10,
                maxPixels=1e9
            ).get('NDVI')
        }))

        results = features.aggregate_array('properties').getInfo()
        return [r for r in results if r.get('ndvi') is not None]

    except Exception as e:
        print(f"❌ Error fetching NDVI data: {e}")
        return []


def export_ndvi_chart(location_name, ndvi_data):
    if not ndvi_data:
        print(f"⚠️ No NDVI data for {location_name}, skipping chart.")
        return

    os.makedirs("output", exist_ok=True)

    try:
        df = pd.DataFrame(ndvi_data)
        if 'date' not in df.columns or 'ndvi' not in df.columns:
            print(f"⚠️ NDVI chart skipped for {location_name}: Missing required columns")
            return

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
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
        "Rainbow_Beach": ee.Geometry.Point([153.1275, -25.9022]),
        "Byron_Bay": ee.Geometry.Point([153.6119, -28.6474])
    }

    for location, geom in locations.items():
        print(f"📍 Processing location: {location}")
        try:
            ndvi_summary = get_ndvi_summary(geom)

            if not ndvi_summary:
                print(f"⚠️ No NDVI summary returned for {location}")
                continue

            print(f"🔍 NDVI summary for {location} (first 2 rows): {ndvi_summary[:2]}")
            export_ndvi_chart(location, ndvi_summary)

        except Exception as e:
            print(f"❌ Failed to process {location}: {e}")

    print("✅ Export script finished.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
