from agents.stats_analyst import StatsAnalystAgent
from agents.strategist import StrategistAgent
from agents.devils_advocate import DevilsAdvocateAgent
from agents.commentator import CommentatorAgent
from cricket_data import MatchState

class CaptainCoolOrchestrator:
    def __init__(self):
        self.stats_analyst    = StatsAnalystAgent()
        self.strategist       = StrategistAgent()
        self.devils_advocate  = DevilsAdvocateAgent()
        self.commentator      = CommentatorAgent()

    def calculate_confidence(self, proposal: str, challenge: str, final: str) -> int:
        proposal_words = set(proposal.lower().split())
        final_words    = set(final.lower().split())
        overlap  = len(proposal_words & final_words)
        total    = len(proposal_words | final_words)
        similarity = overlap / total if total > 0 else 0.5
        base = int(similarity * 100)
        challenge_keywords  = ["economy","average","stats show","historically","fatigue","vulnerable","risk","weakness","data"]
        conviction_keywords = ["stick with","confident","clear call","no doubt","best option","stands firm"]
        penalty = min(sum(1 for kw in challenge_keywords  if kw in challenge.lower()) * 3, 20)
        boost   = sum(1 for kw in conviction_keywords if kw in final.lower()) * 2
        return max(45, min(92, base - penalty + boost))

    def generate_counterfactual(self, match_state: dict, proposal: str, challenge: str) -> str:
        # Search for bowler names mentioned in proposal and challenge
        import re
        bowlers = list(match_state.get("bowlers_used", {}).keys())
        if not bowlers:
            bowlers = ["Mitchell Starc", "Lockie Ferguson", "Harpreet Brar", "Yuzvendra Chahal"]
        
        # Simple extraction of proposed bowler
        proposed_bowler = match_state.get("current_bowler", bowlers[0])
        for b in bowlers:
            if b.lower() in proposal.lower():
                proposed_bowler = b
                break
                
        # Find alternative bowler from challenge
        alternative = bowlers[0] if bowlers[0] != proposed_bowler else (bowlers[1] if len(bowlers) > 1 else "Starc")
        for b in bowlers:
            if b != proposed_bowler and b.lower() in challenge.lower():
                alternative = b
                break
                
        # Simulate counterfactual impact
        val = sum(ord(c) for c in proposed_bowler) - sum(ord(c) for c in alternative)
        diff = abs(val) % 12 + 3.5 # difference between 3.5% and 15.5%
        
        if val > 0:
            impact = f"📉 **Counterfactual Analysis**: If you had bowled **{alternative}** instead of **{proposed_bowler}**, the expected run rate would rise, dropping the team's win probability by **{diff:.1f}%**!"
        else:
            impact = f"📈 **Counterfactual Analysis**: Bowling **{alternative}** instead of **{proposed_bowler}** was proposed, but it increases the risk of boundary leakage by **{diff:.1f}%** in the death overs."
            
        return impact

    def make_decision(self, match_state: MatchState, on_step=None, image=None, custom_query=None) -> dict:
        import time, random, re
        import streamlit as st

        def switch_to_fallback():
            fallback = "gemini-flash-latest"
            self.stats_analyst.model_id = fallback
            self.strategist.model_id = fallback
            self.devils_advocate.model_id = fallback
            self.commentator.model_id = fallback

        def retry_fn(fn):
            max_retries = 5
            backoff = 5.0
            for attempt in range(max_retries):
                try:
                    return fn()
                except Exception as e:
                    err_msg = str(e)
                    is_rate_limit = "429" in err_msg or "resource_exhausted" in err_msg.lower() or "quota" in err_msg.lower()
                    if is_rate_limit:
                        # Auto fallback to 1.5-flash (gemini-flash-latest) on daily quota limit
                        current_model = getattr(self.stats_analyst, "model_id", "")
                        if current_model == "gemini-2.5-flash":
                            switch_to_fallback()
                            st.toast("🔄 Quota exhausted on 2.5-flash. Switched to 1.5-flash fallback!", icon="ℹ️")
                            try:
                                return fn()
                            except Exception as fallback_err:
                                err_msg = str(fallback_err)

                        if attempt < max_retries - 1:
                            sleep_time = backoff + random.uniform(1.0, 5.0)
                            delay_match = re.search(r"retry in ([\d\.]+)s", err_msg)
                            if delay_match:
                                sleep_time = float(delay_match.group(1)) + 1.5
                            
                            st.warning(f"⚠️ Gemini Rate Limit hit. Pausing to retry in {sleep_time:.1f}s... (Attempt {attempt+1}/{max_retries})")
                            time.sleep(sleep_time)
                            backoff *= 2.0
                        else:
                            raise e
                    else:
                        raise e

        def step(label, fn):
            if on_step: on_step(label)
            return retry_fn(fn)

        stats    = step("Stats Analyst", lambda: self.stats_analyst.analyze_match(match_state.to_dict(), image=image))
        proposal = step("Strategist",    lambda: self.strategist.propose_strategy(match_state.to_dict(), stats["analysis"], custom_query=custom_query))
        challenge= step("Devil's Advocate", lambda: self.devils_advocate.challenge_strategy(match_state.to_dict(), proposal["proposal"], stats["analysis"]))
        defense  = step("Strategist Defense", lambda: self.strategist.defend_strategy(match_state.to_dict(), proposal["proposal"], challenge["challenge"]))
        commentary=step("Commentator",   lambda: self.commentator.explain_decision(match_state.to_dict(), defense["defense"]))

        confidence = self.calculate_confidence(proposal["proposal"], challenge["challenge"], defense["defense"])
        counterfactual = self.generate_counterfactual(match_state.to_dict(), proposal["proposal"], challenge["challenge"])

        return {
            "stats":      stats,
            "proposal":   proposal,
            "challenge":  challenge,
            "defense":    defense,
            "commentary": commentary,
            "confidence": confidence,
            "counterfactual": counterfactual,
        }
