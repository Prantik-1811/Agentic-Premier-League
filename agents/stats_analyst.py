import os
import google.generativeai as genai
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
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        self.name = "Stats Analyst"

    def analyze_match(self, match_state: dict) -> dict:
        # Run real tools first
        strike = match_state.get("strike_batter","")
        bowler = match_state.get("current_bowler","")
        venue  = match_state.get("venue","")

        stats   = get_player_stats(strike)
        h2h     = get_head_to_head(strike, bowler)
        weather = get_venue_weather(venue)
        wp      = calculate_win_probability(
            match_state.get("team_batting",""),
            match_state.get("current_score",0),
            match_state.get("wickets_down",0),
            match_state.get("balls_remaining",30),
            match_state.get("target",175),
            match_state.get("pitch_condition","flat"),
            match_state.get("dew_factor",0)
        )

        tool_context = f"""
REAL DATA FETCHED:
Player stats ({strike}): {stats}
Head-to-head ({strike} vs {bowler}): {h2h}
Weather ({venue}): {weather}
Win probability: {wp}
"""
        prompt = f"""{SYSTEM_PROMPT}

Match state:
{match_state}

{tool_context}

Now produce your STATS ANALYST report. Use the real data above."""

        response = self.model.generate_content(prompt)
        return {"agent": self.name, "analysis": response.text, "tool_data": {"stats":stats,"h2h":h2h,"weather":weather,"win_probability":wp}}
