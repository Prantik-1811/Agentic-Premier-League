import os
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are the DEVIL'S ADVOCATE in the IPL war room.
Your job: challenge the Strategist's proposal rigorously. Find flaws. Propose a genuinely better alternative.
Format:
🔴 THE PROBLEM: [What's weak about their proposal — be specific]
💡 ALTERNATIVE: [Different bowler/field/plan and why it's better]
📊 EVIDENCE: [Stats or patterns that back your alternative]
Be tough but constructive. You're making the team's decision stronger."""

class DevilsAdvocateAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-2.5-flash"
        self.name = "Devil's Advocate"

    def challenge_strategy(self, match_state: dict, proposal: str, stats_analysis: str = "") -> dict:
        prompt = f"""Match state: {match_state}\nStats context: {stats_analysis}\nStrategist proposed: {proposal}\n\nNow CHALLENGE this. Find what's wrong. Propose better."""
        response = self.client.models.generate_content(
            model=self.model_id, 
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return {"agent": self.name, "challenge": response.text, "status": "success"}
