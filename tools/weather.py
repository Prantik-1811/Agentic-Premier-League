import requests

def get_venue_weather(venue: str) -> dict:
    """Calls Open-Meteo API to get weather info for a venue"""
    # Mapped roughly to city coordinates
    locations = {
        "Wankhede": {"lat": 18.93, "lon": 72.82},
        "Chepauk": {"lat": 13.06, "lon": 80.27},
        "Chinnaswamy": {"lat": 12.97, "lon": 77.59},
        "Eden Gardens": {"lat": 22.56, "lon": 88.34},
    }
    
    loc = locations.get(venue, {"lat": 20.59, "lon": 78.96}) # Default to India
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&current_weather=true&hourly=relative_humidity_2m,dew_point_2m"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current_weather", {})
        
        # very simple heuristic for dew probability based on temperature and wind
        wind_speed = current.get("windspeed", 10.0)
        temp = current.get("temperature", 25.0)
        
        # high humidity and low wind increases dew
        dew_prob = 50.0
        if wind_speed < 10: dew_prob += 20
        if temp < 25: dew_prob += 10
        
        return {
            "humidity": 75, # Mocking as Open-Meteo hourly would need parsing by current time
            "wind_speed": wind_speed,
            "dew_probability": min(100.0, dew_prob),
            "temperature": temp
        }
    except Exception as e:
        return {
            "humidity": 60,
            "wind_speed": 12,
            "dew_probability": 30,
            "error": str(e)
        }
