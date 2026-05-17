DEVILS_ADVOCATE_PROMPT = """You are the Devil's Advocate.
Challenge the Strategist. Find flaws in their proposal. 
Propose a genuinely different alternative. Provide constructive opposition.
Look for weaknesses in the plan. Suggest a better approach.
"""

def get_devils_advocate():
    try:
        from google_adk import Agent
        return Agent(
            name="Devil's Advocate",
            model="gemini-2.5-pro",
            system_instruction=DEVILS_ADVOCATE_PROMPT,
            tools=[]
        )
    except ImportError:
        class MockAgent:
            async def run(self, *args):
                return "Counter-argument: Siraj might go for runs if the dew factor is 0.7. Bring in Starc instead."
        return MockAgent()
