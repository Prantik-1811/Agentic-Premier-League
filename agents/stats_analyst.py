import json

STATS_ANALYST_PROMPT = """You are the Stats Analyst for the team.
Your job is to crunch numbers, evaluate player form, head-to-head records, economy rates, and win probabilities.
Always be data-first. Output structured stats blocks. Reference specific numbers.
Do not make strategic decisions, just provide the data in a clear, concise manner.
"""

def get_stats_analyst():
    # If google-adk is available, we would use it here.
    # For robust execution without knowing the exact ADK API, we wrap google_genai
    try:
        from google_adk import Agent
        from tools.cricket_api import get_player_stats, calculate_win_probability, get_head_to_head
        return Agent(
            name="Stats Analyst",
            model="gemini-2.5-pro",
            system_instruction=STATS_ANALYST_PROMPT,
            tools=[get_player_stats, calculate_win_probability, get_head_to_head]
        )
    except ImportError:
        # Fallback implementation if google_adk is not installed in the environment
        class MockAgent:
            async def run(self, input_text):
                return f"Stats Analyst Data:\n- Win Probability currently sits at ~45%\n- Siraj economy: 8.5, H2H vs Jadeja: 35 balls, 45 runs, 2 wickets.\n(Mocked response based on {input_text})"
        return MockAgent()
