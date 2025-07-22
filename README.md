
# Coastal Watch Australia

This repository contains a Streamlit dashboard and data pipeline to monitor NDVI and coastline change across Australian coastal sites using Digital Earth Australia (DEA) data.

## 🧱 Structure

- `app.py`: Main Streamlit dashboard
- `alerts.py`: AI risk scoring logic
- `dea_to_dashboard_export.py`: Automated DEA export script
- `data/`: NDVI & coastline data for the dashboard
- `requirements.txt`: Python dependencies

## 🚀 Deployment Instructions

### 1. Clone this repo and install dependencies

```bash
git clone https://github.com/yourusername/coastal-watch-australia.git
cd coastal-watch-australia
pip install -r requirements.txt
```

### 2. Run locally

```bash
streamlit run app.py
```

### 3. Schedule Monthly DEA Data Export

Use cron or a scheduler to run `dea_to_dashboard_export.py` on the 1st of each month.

### 4. Deploy to Streamlit Cloud

- Push this repo to GitHub.
- Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
- Click "New App" → Select this repo → `app.py` as entry point.

You're done ✅

