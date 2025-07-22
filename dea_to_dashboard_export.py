import ee
import os
import pandas as pd
import datetime

# Authenticate and initialize Earth Engine
ee.Authenticate()
ee.Initialize()

# Define multiple locations and bounding boxes
locations = {
    "Rainbow_Beach": {
        "lon_min": 153.05,
        "lon_max": 153.12,
        "lat_min": -25.93,
        "lat_max": -25.88,
    },
    "Byron_Bay": {
        "lon_min": 153.57,
        "lon_max": 153.63,
        "lat_min": -28.67,
        "lat_max": -28.62,
    }
}

def add_indices(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
    return image.addBands([ndvi, ndwi])

# Date range
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
        .map(add_indices)
    )

    median_image = collection.median().clip(geometry)
    ndvi_image = median_image.select('NDVI')
    ndwi_image = median_image.select('NDWI')

    # Export NDVI timeseries
    ndvi_value = ndvi_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10,
        maxPixels=1e9
    ).getInfo().get('NDVI', None)

    ndvi_df = pd.DataFrame([{
        "Date": datetime.date.today().isoformat(),
        "NDVI": ndvi_value
    }])

    ndvi_folder = f"data/NDVI/{loc}"
    os.makedirs(ndvi_folder, exist_ok=True)
    ndvi_df.to_csv(f"{ndvi_folder}/NDVI_timeseries_{loc}.csv", index=False)

    # Generate coastline (NDWI threshold)
    coastline_mask = ndwi_image.gt(0.1).selfMask()
    coastline_vector = coastline_mask.reduceToVectors(
        geometry=geometry,
        scale=10,
        geometryType='line',
        maxPixels=1e9
    )

    # Export GeoJSON
    coastline_geojson = coastline_vector.getInfo()
    coastline_folder = f"data/Coastlines/{loc}"
    os.makedirs(coastline_folder, exist_ok=True)
    with open(f"{coastline_folder}/coastlines_{loc}.geojson", "w") as f:
        import json
        json.dump(coastline_geojson, f)

    print(f"Saved: NDVI and coastline data for {loc}")

print("✅ Earth Engine multi-site NDVI + coastline export complete.")
