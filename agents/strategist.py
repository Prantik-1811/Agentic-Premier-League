import os
import google.generativeai as genai

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
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        self.name = "Strategist"

    def propose_strategy(self, match_state: dict, stats_analysis: str = "") -> dict:
        prompt = f"""{SYSTEM_PROMPT}

Match state: {match_state}
Stats Analyst says: {stats_analysis}

Make your CALL now."""
        response = self.model.generate_content(prompt)
        return {"agent": self.name, "proposal": response.text, "status": "success"}

    def defend_strategy(self, match_state: dict, original: str, challenge: str) -> dict:
        prompt = f"""{SYSTEM_PROMPT}

You proposed:
{original}

Devil's Advocate challenged you with:
{challenge}

Do you STICK WITH IT or REVISE? Respond:
🎤 YOUR RESPONSE: [defend or acknowledge and adjust]
✅ FINAL CALL: [your refined or reaffirmed decision]"""
        response = self.model.generate_content(prompt)
        return {"agent": self.name, "defense": response.text, "status": "success"}
