import os
import google.generativeai as genai

SYSTEM_PROMPT = """You are the DEVIL'S ADVOCATE in the IPL war room.
Your job: challenge the Strategist's proposal rigorously. Find flaws. Propose a genuinely better alternative.
Format:
🔴 THE PROBLEM: [What's weak about their proposal — be specific]
💡 ALTERNATIVE: [Different bowler/field/plan and why it's better]
📊 EVIDENCE: [Stats or patterns that back your alternative]
Be tough but constructive. You're making the team's decision stronger."""

class DevilsAdvocateAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        self.name = "Devil's Advocate"

    def challenge_strategy(self, match_state: dict, proposal: str, stats_analysis: str = "") -> dict:
        prompt = f"""{SYSTEM_PROMPT}

Match state: {match_state}
Stats context: {stats_analysis}
Strategist proposed: {proposal}

Now CHALLENGE this. Find what's wrong. Propose better."""
        response = self.model.generate_content(prompt)
        return {"agent": self.name, "challenge": response.text, "status": "success"}
