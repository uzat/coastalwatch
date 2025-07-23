import os
import json
import base64
import ee
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


# === Config ===
USE_SCL_MASKING = True  # Set False to use probability-based cloud masking
NDVI_DAYS_INTERVAL = 14


def initialize_earth_engine():
    b64 = os.environ.get("EARTHENGINE_SERVICE_ACCOUNT_JSON")
    if not b64:
        raise Exception("EARTHENGINE_SERVICE_ACCOUNT_JSON not found in environment variables.")
    decoded = base64.b64decode(b64).decode("utf-8")
    credentials_json = json.loads(decoded)
    credentials = ee.ServiceAccountCredentials(
        email=credentials_json["client_email"],
        key_data=json.dumps(credentials_json)
    )
    ee.Initialize(credentials)
    print("✅ Earth Engine initialized successfully.")


def mask_clouds_scl(image):
    scl = image.select("SCL")
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


def mask_clouds_probability(image):
    cloud_prob = image.select("MSK_CLDPRB")
    return image.updateMask(cloud_prob.lt(30))


def calculate_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


def get_ndvi_time_series(aoi, start_date, end_date):
    collection = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50)) \
        .map(mask_clouds_scl if USE_SCL_MASKING else mask_clouds_probability) \
        .map(calculate_ndvi)

    def reduce_image(image):
        date = ee.Date(image.get("system:time_start")).format("YYYY-MM-dd")
        mean = image.select("NDVI").reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=10
        ).get("NDVI")
        return ee.Feature(None, {"date": date, "ndvi": mean})

    features = collection.map(reduce_image).filter(
        ee.Filter.notNull(["ndvi"])
    ).aggregate_array("properties")

    results = features.getInfo()
    if not results:
        return []

    return [{"date": f["date"], "ndvi": f["ndvi"]} for f in results]


def export_ndvi_chart(location_name, ndvi_data):
    os.makedirs("output", exist_ok=True)
    try:
        df = pd.DataFrame(ndvi_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        plt.figure(figsize=(10, 5))
        plt.plot(df["date"], df["ndvi"], marker="o")
        plt.title(f"NDVI Time Series – {location_name.replace("_", " ")}")
        plt.xlabel("Date")
        plt.ylabel("NDVI")
        plt.grid(True)
        plt.tight_layout()
        path = f"output/{location_name}_ndvi_chart.png"
        plt.savefig(path)
        plt.close()
        print(f"📈 Saved chart: {path}")
    except Exception as e:
        print(f"⚠️ Failed to create chart for {location_name}: {e}")


def export_summary_csv(location_name, ndvi_data):
    try:
        folder = f"data/NDVI/{location_name}"
        os.makedirs(folder, exist_ok=True)
        df = pd.DataFrame(ndvi_data)
        path = f"{folder}/ndvi_summary_{location_name}.csv"
        df.to_csv(path, index=False)
        print(f"📄 Saved NDVI summary: {path}")
    except Exception as e:
        print(f"⚠️ Failed to save summary for {location_name}: {e}")


def main():
    initialize_earth_engine()

    locations = {
        "Rainbow_Beach": ee.Geometry.Point([153.138, -25.904]),
        "Byron_Bay": ee.Geometry.Point([153.61, -28.647]),
    }

    start_date = "2024-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    for loc_name, geom in locations.items():
        print(f"📍 Processing location: {loc_name}")
        try:
            ndvi_data = get_ndvi_time_series(geom, start_date, end_date)
            if not ndvi_data:
                print(f"⚠️ No NDVI summary returned for {loc_name}")
                continue
            export_summary_csv(loc_name, ndvi_data)
            export_ndvi_chart(loc_name, ndvi_data)
        except Exception as e:
            print(f"❌ Failed to process {loc_name}: {e}")


if __name__ == "__main__":
    main()
