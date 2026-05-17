import os
import google.generativeai as genai

SYSTEM_PROMPT = """You are a seasoned IPL commentator — think Harsha Bhogle meets Wasim Akram.
Translate the captain's decision into cricket-speak that any fan understands.
Format:
📺 THE CALL EXPLAINED: [2-3 sentences of pure cricket narrative]
🧠 WHY THIS, NOT THAT:
  • Not [Alternative 1]: [reason]
  • Not [Alternative 2]: [reason]
  • YES this: [decisive factor]
🎬 THE NARRATIVE: [How this fits the match story — momentum, psychology, pressure]
No ML jargon. No percentages in prose. Just cricket."""

class CommentatorAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        self.name = "Match Commentator"

    def explain_decision(self, match_state: dict, final_decision: str) -> dict:
        prompt = f"""{SYSTEM_PROMPT}

Match state: {match_state}
Captain's final decision: {final_decision}

Explain this like you're on air. Make fans believe in it."""
        response = self.model.generate_content(prompt)
        return {"agent": self.name, "commentary": response.text, "status": "success"}
