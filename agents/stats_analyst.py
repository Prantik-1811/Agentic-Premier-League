import os
from google import genai
from google.genai import types
from tools.cricket_api import get_player_stats, get_head_to_head, calculate_win_probability
from tools.weather import get_venue_weather

SYSTEM_PROMPT = """You are the STATS ANALYST in an IPL captain's war room.
Your role: Crunch numbers. Surface player form, head-to-head records, economy rates, win probability.
Output format:
1. KEY STATS — specific numbers only
2. PATTERN ANALYSIS — what the data reveals
3. WIN PROBABILITY — current % for the batting team
4. RECOMMENDED FOCUS — what the Strategist must consider
Speak in cricket statistics. Be precise. No filler."""

class StatsAnalystAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-2.5-flash"
        self.name = "Stats Analyst"

    def analyze_match(self, match_state: dict) -> dict:
        prompt = f"""Match state:
{match_state}

Please use your tools to fetch:
1. Venue weather for '{match_state.get('venue', '')}'
2. Player stats for batter '{match_state.get('strike_batter', '')}'
3. Head-to-head for '{match_state.get('strike_batter', '')}' vs '{match_state.get('current_bowler', '')}'
4. Win probability (using team_batting='{match_state.get('team_batting', '')}', score={match_state.get('current_score', 0)}, wickets={match_state.get('wickets_down', 0)}, balls_remaining={match_state.get('balls_remaining', 30)}, target={match_state.get('target', 175)})

After fetching the real data via tools, produce your STATS ANALYST report."""

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[get_venue_weather, get_player_stats, get_head_to_head, calculate_win_probability],
                temperature=0.2
            )
        )
        return {"agent": self.name, "analysis": response.text, "status": "success"}
