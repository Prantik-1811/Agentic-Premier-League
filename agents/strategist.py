STRATEGIST_PROMPT = """You are the Strategist. Think like MS Dhoni.
You make the call: Next bowler, field placement, timeout, Impact Player decision.
Be bold, decisive, cricket-smart. No waffling. 
Take input from the Stats Analyst and Match State to formulate a winning plan.
"""

def get_strategist():
    try:
        from google_adk import Agent
        from tools.cricket_api import get_venue_weather
        return Agent(
            name="Strategist",
            model="gemini-2.5-pro",
            system_instruction=STRATEGIST_PROMPT,
            tools=[get_venue_weather]
        )
    except ImportError:
        class MockAgent:
            async def run(self, *args):
                return "Captain's Call: Bowl Siraj. Keep mid-off up. Use the turning pitch to cramp Jadeja."
        return MockAgent()
