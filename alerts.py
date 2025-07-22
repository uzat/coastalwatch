# AI-powered alert logic module

# alerts.py
def get_risk_level(ndvi_df):
    if len(ndvi_df) < 2:
        return "Unknown"
    delta = ndvi_df["NDVI"].iloc[-1] - ndvi_df["NDVI"].iloc[0]
    if delta < -0.2:
        return "🔴 High Risk"
    elif delta < -0.1:
        return "🟠 Watch"
    else:
        return "🟢 Stable"

