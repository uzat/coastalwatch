# DEA export script placeholder
"""
DEA to Dashboard Export Pipeline
Exports NDVI GeoTIFF, NDVI CSV, and Coastline GeoJSON
"""

import os
import datacube
from dea_tools.bandindices import calculate_indices
from dea_tools.datahandling import load_ard
from dea_tools.coastal import retrieve_coastlines
from datacube.utils.geometry import Geometry
import xarray as xr

# Connect to DEA
dc = datacube.Datacube(app="dea_to_dashboard_export")

# Define locations (add more if needed)
locations = {
    "Rainbow_Beach": {
        "lat_min": -25.915, "lat_max": -25.880,
        "lon_min": 153.078, "lon_max": 153.145
    }
}

# Define time range
time_range = ("2017-01", "2024-06")

# Set base output folder
base_export = "data"

for name, coords in locations.items():
    print(f"\n📍 Processing: {name}")

    lat_min, lat_max = coords["lat_min"], coords["lat_max"]
    lon_min, lon_max = coords["lon_min"], coords["lon_max"]

    # Prepare folders
    ndvi_dir = os.path.join(base_export, "NDVI", name)
    coast_dir = os.path.join(base_export, "Coastlines", name)
    os.makedirs(ndvi_dir, exist_ok=True)
    os.makedirs(coast_dir, exist_ok=True)

    # Load ARD satellite data
    ds = load_ard(
        dc=dc,
        products=["s2_l2a"],
        measurements=["red", "nir"],
        x=(lon_min, lon_max),
        y=(lat_min, lat_max),
        time=time_range,
        output_crs="EPSG:3577",
        resolution=(-10, 10),
        group_by="solar_day",
        dask_chunks={"time": 1}
    )

    if ds.time.size == 0:
        print("⚠️ No data found — skipping.")
        continue

    # Calculate NDVI
    ds = calculate_indices(ds, index="NDVI", collection="ga_s2_2", drop=False)

    # Export NDVI GeoTIFF (first scene only)
    print("🛰️ Saving NDVI GeoTIFF...")
    ndvi_path = os.path.join(ndvi_dir, f"NDVI_{name}_scene1.tif")
    ds.NDVI.isel(time=0).rio.to_raster(ndvi_path)

    # Export NDVI time series (CSV)
    print("📈 Saving NDVI timeseries...")
    ndvi_mean = ds.NDVI.mean(dim=["x", "y"]).compute()
    csv_path = os.path.join(ndvi_dir, f"NDVI_timeseries_{name}.csv")
    ndvi_mean.to_dataframe(name="NDVI").to_csv(csv_path)

    # Generate geometry for coastline extraction
    print("🌊 Saving coastline vector...")
    geom = Geometry(
        geom={"type": "Polygon", "coordinates": [[
            [lon_min, lat_min],
            [lon_min, lat_max],
            [lon_max, lat_max],
            [lon_max, lat_min],
            [lon_min, lat_min]
        ]]},
        crs="EPSG:4326"
    )

    # Retrieve and save coastline GeoJSON
    coastlines = retrieve_coastlines(
        dc=dc,
        polygon=geom,
        time_range=time_range,
        min_beach_area=1000,
        baseline="median"
    )
    geojson_path = os.path.join(coast_dir, f"coastlines_{name}.geojson")
    coastlines.gdf.to_file(geojson_path, driver="GeoJSON")

    print("✅ Export complete for", name)

print("\n🎉 All locations exported. Dashboard is ready to refresh.")
