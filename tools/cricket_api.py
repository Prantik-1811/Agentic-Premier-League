import requests
from bs4 import BeautifulSoup
import math

def fetch_live_match_state(cricbuzz_url: str) -> dict:
    """Scrapes Cricbuzz/ESPNCricinfo URL for basic match stats"""
    # Mock implementation as a real scraper would break or need maintenance
    return {
        "innings": 2,
        "over": 15,
        "score": 98,
        "wickets": 4,
        "batters": ["Jadeja", "Moeen Ali"],
        "bowlers": ["Siraj"],
        "RRR": 15.4
    }

def calculate_win_probability(batting_team: str, score: int, wickets: int, balls_remaining: int, target: int, pitch: str) -> float:
    """Uses a heuristic formula to calculate win probability"""
    if target == 0:
        return 0.5
    runs_needed = target - score
    if runs_needed <= 0: return 1.0
    if balls_remaining == 0: return 0.0
    
    req_rate = (runs_needed / balls_remaining) * 6
    baseline_prob = 1.0 - (runs_needed / target)
    
    # Heuristic adjustment
    wicket_factor = 1.0 - (wickets / 10.0)
    rate_factor = min(1.0, 8.0 / req_rate) if req_rate > 0 else 1.0
    
    prob = baseline_prob * 0.4 + wicket_factor * 0.4 + rate_factor * 0.2
    return max(0.01, min(0.99, prob))

def get_player_stats(player_name: str, context: str) -> dict:
    """Returns basic IPL stats"""
    stats = {
        "Jadeja": {"avg": 26.5, "SR": 128.5, "economy": 7.6, "recent_form": "good"},
        "Siraj": {"avg": 28.0, "SR": 18.0, "economy": 8.5, "recent_form": "average"},
    }
    return stats.get(player_name, {"avg": 25.0, "SR": 130.0, "economy": 8.0, "recent_form": "unknown"})

def get_head_to_head(batter: str, bowler: str) -> dict:
    """Returns head to head stats"""
    return {
        "balls_faced": 35,
        "runs": 45,
        "dismissals": 2,
        "avg": 22.5
    }

def get_venue_weather(venue: str) -> dict:
    """Gets weather for a venue"""
    import random
    return {
        "humidity": random.randint(60, 90),
        "wind_speed": random.randint(5, 15),
        "dew_probability": random.randint(40, 80)
    }
