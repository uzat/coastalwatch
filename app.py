# Streamlit app entry point
import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.plot import reshape_as_image
import plotly.express as px
import folium
from streamlit_folium import st_folium
from alerts import get_risk_level  # assumes you have alerts.py

# --- Page config ---
st.set_page_config(layout="wide")
st.title("🌊 Coastal Watch Australia")

# --- Load locations from folders ---
NDVI_ROOT = "data/NDVI"
COAST_ROOT = "data/Coastlines"

locations = sorted([
    name for name in os.listdir(NDVI_ROOT)
    if os.path.isdir(os.path.join(NDVI_ROOT, name))
])

if not locations:
    st.error("No locations found in data/NDVI/")
    st.stop()

location = st.sidebar.selectbox("📍 Select Location", locations)

# --- Paths ---
ndvi_folder = os.path.join(NDVI_ROOT, location)
coast_folder = os.path.join(COAST_ROOT, location)
ndvi_csv_path = os.path.join(ndvi_folder, f"NDVI_timeseries_{location}.csv")
ndvi_tif_path = os.path.join(ndvi_folder, f"NDVI_{location}_scene1.tif")
coast_geojson_path = os.path.join(coast_folder, f"coastlines_{location}.geojson")

# --- AI RISK SCORE ---
st.sidebar.subheader("🧠 Risk Status")
try:
    ndvi_data = pd.read_csv(ndvi_csv_path, index_col=0)
    risk = get_risk_level(ndvi_data)
    st.sidebar.success(f"Site Status: {risk}")
except Exception as e:
    st.sidebar.error(f"Risk model error: {e}")

# --- NDVI Time Series Plot ---
try:
    st.subheader("🌿 NDVI Time Series")
    fig = px.line(ndvi_data, y="NDVI", title=f"{location.replace('_', ' ')} — NDVI over Time")
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"NDVI CSV error: {e}")

# --- NDVI GeoTIFF Preview ---
try:
    with rasterio.open(ndvi_tif_path) as src:
        arr = src.read(1)
    fig2 = px.imshow(arr, color_continuous_scale="Greens", origin="upper")
    fig2.update_layout(title="NDVI Map", coloraxis_colorbar=dict(title="NDVI"))
    st.plotly_chart(fig2, use_container_width=True)
except Exception as e:
    st.warning(f"NDVI TIFF error: {e}")

# --- Coastline GeoJSON Preview ---
try:
    st.subheader("🌐 Coastline Change Map")
    gdf = gpd.read_file(coast_geojson_path)
    center = gdf.unary_union.centroid
    fmap = folium.Map(location=[center.y, center.x], zoom_start=13)
    folium.GeoJson(gdf).add_to(fmap)
    st_folium(fmap, height=450, width=700)
except Exception as e:
    st.warning(f"Coastline map error: {e}")

# --- Download Section ---
st.sidebar.subheader("⬇️ Downloads")
if os.path.exists(ndvi_csv_path):
    st.sidebar.download_button("Download NDVI CSV", open(ndvi_csv_path, 'rb'), file_name="ndvi_timeseries.csv")
if os.path.exists(coast_geojson_path):
    st.sidebar.download_button("Download Coastline GeoJSON", open(coast_geojson_path, 'rb'), file_name="coastline.geojson")

