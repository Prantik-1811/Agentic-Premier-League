import os
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are the STRATEGIST — the IPL captain in the war room.
Think like Dhoni: calm, calculated, bold. You make THE CALL.
Format:
🎯 THE CALL:
  • Next Bowler: [Name — one line reason]
  • Field Setup: [Key placements]
  • Strategy: [Plan for next 2-3 overs]
  • Timeout: Yes/No [why]
  • Impact Player: Yes/No [when]
🧠 THE REASONING: [2-3 sentences of cricket logic]
⚠️ RISKS: [What could go wrong and how you handle it]
Be decisive. No waffling. Be ready to defend."""

class StrategistAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-2.5-flash"
        self.name = "Strategist"

    def propose_strategy(self, match_state: dict, stats_analysis: str = "", custom_query: str = None) -> dict:
        query_text = f"\nUser Question/Command: {custom_query}\nAnswer this command/question directly in your strategy." if custom_query else ""
        prompt = f"""Match state: {match_state}\nStats Analyst says: {stats_analysis}{query_text}\n\nMake your CALL now."""
        response = self.client.models.generate_content(
            model=self.model_id, 
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return {"agent": self.name, "proposal": response.text, "status": "success"}

    def defend_strategy(self, match_state: dict, original: str, challenge: str) -> dict:
        prompt = f"""You proposed:\n{original}\n\nDevil's Advocate challenged you with:\n{challenge}\n\nDo you STICK WITH IT or REVISE? Respond:\n🎤 YOUR RESPONSE: [defend or acknowledge and adjust]\n✅ FINAL CALL: [your refined or reaffirmed decision]"""
        response = self.client.models.generate_content(
            model=self.model_id, 
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return {"agent": self.name, "defense": response.text, "status": "success"}
