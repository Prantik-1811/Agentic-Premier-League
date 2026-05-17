COMMENTATOR_PROMPT = """You are the Match Commentator. Think Harsha Bhogle.
Translate the final decision into TV-style cricket commentary.
Use cricket-speak only. No ML jargon. Add narrative and emotion.
"""

def get_commentator():
    try:
        from google_adk import Agent
        return Agent(
            name="Match Commentator",
            model="gemini-2.5-pro",
            system_instruction=COMMENTATOR_PROMPT,
            tools=[]
        )
    except ImportError:
        class MockAgent:
            async def run(self, *args):
                return "Oh, what a masterstroke! The captain has decided to back his premier fast bowler in the death. The field is set, the crowd is buzzing. Can Siraj deliver?"
        return MockAgent()
