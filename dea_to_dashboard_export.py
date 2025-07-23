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

def mask_s2_sr(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask)

def compute_ndvi_timeseries(location_name, region):
    start_date = "2024-01-01"
    end_date = datetime.today().strftime('%Y-%m-%d')
    s2 = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterDate(start_date, end_date) \
        .filterBounds(region) \
        .map(mask_s2_sr) \
        .map(lambda img: img.addBands(img.normalizedDifference(['B8', 'B4']).rename('NDVI')))
    size = s2.size().getInfo()
    print(f"📸 Found {size} Sentinel-2 images for {location_name}")
    if size == 0:
        return []
    def extract_ndvi(image):
        date = image.date().format('YYYY-MM-dd')
        mean = image.select('NDVI').reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region, scale=10, maxPixels=1e9
        ).get('NDVI')
        return ee.Feature(None, {'date': date, 'ndvi': mean})
    features = ee.FeatureCollection(s2.map(extract_ndvi)).getInfo()["features"]
    return [f["properties"] for f in features if f["properties"].get("ndvi") is not None]

def export_ndvi_results(location_name, ndvi_data):
    folder = f"data/NDVI/{location_name}"
    os.makedirs(folder, exist_ok=True)
    if not ndvi_data:
        print(f"⚠️ No NDVI data for {location_name}, skipping export.")
        return
    df = pd.DataFrame(ndvi_data)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values("date")
    csv_path = f"{folder}/ndvi_summary_{location_name}.csv"
    df.to_csv(csv_path, index=False)
    plt.figure(figsize=(10, 5))
    plt.plot(df['date'], df['ndvi'], marker='o')
    plt.title(f"NDVI Time Series – {location_name.replace('_', ' ')}")
    plt.xlabel("Date")
    plt.ylabel("NDVI")
    plt.grid(True)
    plt.tight_layout()
    chart_path = f"{folder}/ndvi_chart_{location_name}.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"✅ Exported CSV & chart for {location_name}")

def main():
    initialize_earth_engine()
    locations = {
        "Rainbow_Beach": ee.Geometry.Polygon([
            [[153.093, -25.902], [153.093, -25.812], [153.203, -25.812], [153.203, -25.902]]
        ]),
        "Byron_Bay": ee.Geometry.Polygon([
            [[153.580, -28.680], [153.580, -28.610], [153.640, -28.610], [153.640, -28.680]]
        ])
    }
    for name, geom in locations.items():
        print(f"📍 Processing location: {name}")
        data = compute_ndvi_timeseries(name, geom)
        export_ndvi_results(name, data)
    print("✅ Export script finished.")

if __name__ == "__main__":
    main()
