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

    def make_decision(self, match_state: MatchState, on_step=None) -> dict:
        def step(label, fn):
            if on_step: on_step(label)
            return fn()

        stats    = step("Stats Analyst", lambda: self.stats_analyst.analyze_match(match_state.to_dict()))
        proposal = step("Strategist",    lambda: self.strategist.propose_strategy(match_state.to_dict(), stats["analysis"]))
        challenge= step("Devil's Advocate", lambda: self.devils_advocate.challenge_strategy(match_state.to_dict(), proposal["proposal"], stats["analysis"]))
        defense  = step("Strategist Defense", lambda: self.strategist.defend_strategy(match_state.to_dict(), proposal["proposal"], challenge["challenge"]))
        commentary=step("Commentator",   lambda: self.commentator.explain_decision(match_state.to_dict(), defense["defense"]))

        confidence = self.calculate_confidence(proposal["proposal"], challenge["challenge"], defense["defense"])

        return {
            "stats":      stats,
            "proposal":   proposal,
            "challenge":  challenge,
            "defense":    defense,
            "commentary": commentary,
            "confidence": confidence,
        }
