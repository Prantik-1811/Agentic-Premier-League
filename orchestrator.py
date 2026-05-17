import asyncio
import random
from agents.stats_analyst import get_stats_analyst
from agents.strategist import get_strategist
from agents.devils_advocate import get_devils_advocate
from agents.commentator import get_commentator
from cricket_data import MatchState

stats_analyst = get_stats_analyst()
strategist = get_strategist()
devils_advocate = get_devils_advocate()
commentator = get_commentator()

def calculate_confidence(proposal, challenge, final):
    # Mock confidence calculation based on string lengths and random variance
    base = 75
    variance = random.randint(-15, 20)
    return max(0, min(100, base + variance))

async def captain_decision(match_state: MatchState):
    """
    The main multi-agent debate loop.
    Yields intermediate results for the UI to stream.
    """
    state_str = str(match_state.to_dict())
    
    # Round 1: Intelligence gathering
    yield {"step": "stats_analyst", "status": "running"}
    stats = await stats_analyst.run(state_str)
    yield {"step": "stats_analyst", "status": "done", "content": stats}
    
    # Round 2: Initial proposal
    yield {"step": "strategist_initial", "status": "running"}
    proposal = await strategist.run(f"Match State: {state_str}\nStats: {stats}")
    yield {"step": "strategist_initial", "status": "done", "content": proposal}
    
    # Round 3: Challenge
    yield {"step": "devils_advocate", "status": "running"}
    challenge = await devils_advocate.run(f"Stats: {stats}\nProposal: {proposal}")
    yield {"step": "devils_advocate", "status": "done", "content": challenge}
    
    # Round 4: Defense/Revision
    yield {"step": "strategist_final", "status": "running"}
    final = await strategist.run(f"Initial Proposal: {proposal}\nChallenge: {challenge}\nRevise and finalize your decision.")
    yield {"step": "strategist_final", "status": "done", "content": final}
    
    # Round 5: Commentary
    yield {"step": "commentator", "status": "running"}
    comment = await commentator.run(f"Match State: {state_str}\nFinal Decision: {final}")
    yield {"step": "commentator", "status": "done", "content": comment}
    
    # Final Summary Output
    yield {
        "step": "final_summary",
        "status": "done",
        "content": {
            "stats_analysis": stats,
            "initial_proposal": proposal,
            "challenge": challenge,
            "final_decision": final,
            "commentary": comment,
            "confidence_score": calculate_confidence(proposal, challenge, final)
        }
    }
