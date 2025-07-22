import ee
import os
import pandas as pd
import datetime

# Authenticate and initialize Earth Engine
ee.Authenticate()
ee.Initialize()

# Define locations and bounding boxes
locations = {
    "Rainbow_Beach": {
        "lon_min": 153.05,
        "lon_max": 153.12,
        "lat_min": -25.93,
        "lat_max": -25.88,
    }
}

# Function to calculate NDVI for a given image
def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')  # Sentinel-2 bands
    return image.addBands(ndvi)

# Set export date range
start_date = '2024-01-01'
end_date = '2024-12-31'

for loc, bounds in locations.items():
    print(f"Processing {loc}...")

    geometry = ee.Geometry.Rectangle([
        bounds["lon_min"], bounds["lat_min"],
        bounds["lon_max"], bounds["lat_max"]
    ])

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start_date, end_date)
        .filterBounds(geometry)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(add_ndvi)
    )

    # Reduce the collection to median NDVI image
    ndvi_image = collection.select('NDVI').median().clip(geometry)

    # Create folder structure
    ndvi_folder = f"data/NDVI/{loc}"
    os.makedirs(ndvi_folder, exist_ok=True)

    # Export NDVI as CSV
    ndvi_reduced = ndvi_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10,
        maxPixels=1e9
    )

    ndvi_value = ndvi_reduced.getInfo().get('NDVI', None)
    ndvi_df = pd.DataFrame([{
        "Date": datetime.date.today().isoformat(),
        "NDVI": ndvi_value
    }])

    ndvi_csv_path = f"{ndvi_folder}/NDVI_timeseries_{loc}.csv"
    ndvi_df.to_csv(ndvi_csv_path, index=False)

    print(f"Saved: {ndvi_csv_path}")

print("✅ Earth Engine NDVI export complete.")
