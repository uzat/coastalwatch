import os
import json
import base64
import ee
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 🔁 Config
LOCATIONS = {
    "Rainbow_Beach": {"lat": -25.9, "lon": 153.1},
    "Byron_Bay": {"lat": -28.6, "lon": 153.6}
}
USE_SCL_MASK = False  # ✅ Set to False to use cloud probability masking instead
DATA_DIR = "data/NDVI"

# 🔐 Init Earth Engine from base64 secret
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
        exit(1)

# 🌥 Cloud masking (SCL method)
def mask_clouds_scl(image):
    scl = image.select('SCL')
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)

# 🌥 Cloud masking (cloud probability method)
def mask_clouds_probability(image):
    prob = image.select('MSK_CLDPRB')
    return image.updateMask(prob.lt(30))

# 🛰 Fetch NDVI timeseries
def get_ndvi_series(lat, lon, location_name):
    point = ee.Geometry.Point([lon, lat])
    collection = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(point) \
        .filterDate("2024-01-01", "2025-01-01") \
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40)) \
        .select(["B4", "B8", "SCL", "MSK_CLDPRB"])

    # Apply selected mask
    if USE_SCL_MASK:
        collection = collection.map(mask_clouds_scl)
    else:
        collection = collection.map(mask_clouds_probability)

    def compute_ndvi(image):
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        date = image.date().format("YYYY-MM-dd")
        return ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10
        ).set("date", date)

    ndvi_results = collection.map(compute_ndvi).filter(ee.Filter.notNull(["NDVI"]))
    features = ndvi_results.aggregate_array("NDVI").getInfo()
    dates = ndvi_results.aggregate_array("date").getInfo()

    if not dates or not features:
        return []

    return [{"date": d, "ndvi": n} for d, n in zip(dates, features)]

# 📊 Save chart
def save_chart(location, data):
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values("date")

    plt.figure(figsize=(10, 5))
    plt.plot(df['date'], df['ndvi'], marker='o')
    plt.title(f"NDVI Time Series – {location.replace('_', ' ')}")
    plt.xlabel("Date")
    plt.ylabel("NDVI")
    plt.grid(True)
    plt.tight_layout()

    path = f"output/{location}_ndvi_chart.png"
    plt.savefig(path)
    plt.close()
    print(f"📈 Saved NDVI chart to {path}")

# 📁 Save CSV
def save_csv(location, data):
    folder = os.path.join(DATA_DIR, location)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"ndvi_summary_{location}.csv")
    pd.DataFrame(data).to_csv(path, index=False)
    print(f"📄 Saved NDVI CSV to {path}")

# 🧠 Main logic
def main():
    initialize_earth_engine()

    for name, coords in LOCATIONS.items():
        print(f"📍 Processing location: {name}")
        try:
            ndvi_data = get_ndvi_series(coords["lat"], coords["lon"], name)
            if not ndvi_data:
                print(f"⚠️ No NDVI summary returned for {name}")
                continue
            save_csv(name, ndvi_data)
            save_chart(name, ndvi_data)
        except Exception as e:
            print(f"❌ Failed to process {name}: {e}")

    print("✅ Export script finished.")

if __name__ == "__main__":
    main()
