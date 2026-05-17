from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class MatchState:
    innings: int
    over: int
    ball: int
    team_batting: str
    team_bowling: str
    current_score: int
    wickets_down: int
    strike_batter: str
    strike_batter_runs: int
    strike_batter_balls: int
    non_strike_batter: str
    non_strike_batter_runs: int
    non_strike_batter_balls: int
    current_bowler: str
    bowlers_used: Dict[str, float]
    pitch_condition: str
    dew_factor: float
    venue: str
    target: int
    balls_remaining: int
    required_run_rate: float
    impact_player_available: bool
    timeouts_left: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
