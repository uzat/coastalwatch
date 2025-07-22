# coastalwatch

# 🌊 Coastal Watch Australia

Coastal Watch Australia is a Streamlit-powered dashboard that visualizes NDVI (vegetation health) and coastline change across key Australian coastal locations. It integrates with **Digital Earth Australia (DEA)** to automatically extract and update environmental monitoring data.

---

## 📦 Features

- 🛰️ NDVI trend analysis using Sentinel-2 imagery (via DEA)
- 🌐 Coastline change detection from DEA’s coastline datasets
- 🔔 AI-powered alerts for erosion and vegetation degradation
- 🗺️ Interactive map + plots for each monitored location
- 📤 Scheduled monthly export pipeline for automated updates

---

## 📁 Folder Structure
coastal-watch-australia/
├── app.py # Streamlit dashboard interface
├── alerts.py # Erosion/NDVI alert scoring logic
├── dea_to_dashboard_export.py # DEA data export script
├── requirements.txt # Python dependencies
├── data/
│ ├── NDVI/
│ │ └── Rainbow_Beach/
│ │ ├── NDVI_scene1.tif
│ │ └── NDVI_timeseries_Rainbow_Beach.csv
│ └── Coastlines/
│ └── Rainbow_Beach/
│ └── coastlines_Rainbow_Beach.geojson
└── README.md


---

## 🚀 Quickstart Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<yourusername>/coastal-watch-australia.git
cd coastal-watch-australia

### 2. Install Dependencies
pip install -r requirements.txt

### 3. Run the Dashboard Locally
streamlit run app.py

### 4. Deploy to Streamlit Cloud
Push this repo to GitHub

Go to https://streamlit.io/cloud

Click “New App” → Select your repo → Set app.py as the entry point

Click “Deploy” – you're live!
