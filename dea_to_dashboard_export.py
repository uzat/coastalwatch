import os
import json
import base64
import ee

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
        raise Exception(f"Failed to initialize Earth Engine: {str(e)}")


def export_ndvi_chart(location_name, ndvi_data):
    os.makedirs("output", exist_ok=True)

    try:
        df = pd.DataFrame(ndvi_data)
        df['date'] = pd.to_datetime(df['date'])
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

    locations = ["Rainbow_Beach", "Byron_Bay"]  # Add more as needed
    for location in locations:
        print(f"📍 Processing location: {location}")

        # Simulate NDVI data retrieval – replace this block with actual Earth Engine export
        # Your real NDVI data export function should return a list of dicts like:
        # [{"date": "2024-01-01", "ndvi": 0.67}, ...]
        dummy_data = [
            {"date": "2024-01-01", "ndvi": 0.55},
            {"date": "2024-02-01", "ndvi": 0.60},
            {"date": "2024-03-01", "ndvi": 0.62},
        ]

        export_ndvi_chart(location, dummy_data)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Failed to initialize Earth Engine: {e}")
