import requests

VENUE_COORDS = {
    "wankhede":              (18.9388, 72.8258),
    "eden gardens":          (22.5645, 88.3433),
    "chinnaswamy":           (12.9789, 77.5996),
    "chepauk":               (13.0635, 80.2790),
    "narendra modi":         (23.0900, 72.5970),
    "feroz shah kotla":      (28.6362, 77.2410),
    "punjab cricket":        (30.6942, 76.8606),
    "rajiv gandhi hyderabad":(17.4032, 78.4008),
    "sawai mansingh":        (26.9124, 75.7873),
    "barsapara":             (26.1589, 91.6514),
}

def get_venue_weather(venue: str) -> dict:
    key = venue.lower().strip()
    coords = next((v for k, v in VENUE_COORDS.items() if k in key or key in k), None)
    if not coords:
        return {"error": f"Venue '{venue}' not in database", "dew_risk": "unknown"}
    lat, lon = coords
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"
        f"&forecast_days=1&timezone=Asia%2FKolkata"
    )
    try:
        data = requests.get(url, timeout=10).json()
        c = data.get("current", {})
        humidity = c.get("relative_humidity_2m", 0)
        wind     = c.get("wind_speed_10m", 0)
        temp     = c.get("temperature_2m", 25)
        precip   = c.get("precipitation", 0)
        dew_score = (humidity / 100) * (1 - min(wind / 20, 1))
        dew_risk  = "high" if dew_score > 0.65 else "medium" if dew_score > 0.35 else "low"
        return {
            "venue": venue, "temperature_c": temp, "humidity_pct": humidity,
            "wind_kmh": wind, "precipitation_mm": precip,
            "dew_risk": dew_risk, "dew_risk_score": round(dew_score, 2),
            "impact": (
                "Dew heavily favors batting — bowlers will lose grip after over 15"
                if dew_risk == "high" else
                "Some dew expected — monitor grip in death overs"
                if dew_risk == "medium" else
                "Dry conditions — pitch behavior consistent both innings"
            )
        }
    except Exception as e:
        return {"error": str(e), "venue": venue, "dew_risk": "unknown"}
