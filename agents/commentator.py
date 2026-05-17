import os
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are the MATCH COMMENTATOR (think Harsha Bhogle or Ian Bishop).
Your job: Explain the final strategic decision to the TV audience in pure cricket terminology.
Format:
🎙️ ON AIR: [1-2 paragraphs explaining the tactical nuance of the decision, the match situation, and why the captain went this route.]
Make it sound exciting, insightful, and accessible."""

class CommentatorAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-2.5-flash"
        self.name = "Match Commentator"

    def explain_decision(self, match_state: dict, final_decision: str) -> dict:
        prompt = f"""Match state: {match_state}\nFinal Decision by Captain: {final_decision}\n\nDeliver your commentary."""
        response = self.client.models.generate_content(
            model=self.model_id, 
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return {"agent": self.name, "commentary": response.text, "status": "success"}
