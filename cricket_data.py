from dataclasses import dataclass, asdict
from typing import Optional, Dict

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
    target: Optional[int]
    balls_remaining: int
    required_run_rate: float
    impact_player_available: bool
    timeouts_left: int

    def to_dict(self):
        return asdict(self)

    def to_readable_string(self) -> str:
        return f"""
MATCH STATE
==================================================
Innings: {self.innings}/2 | Over: {self.over}.{self.ball} | Balls left: {self.balls_remaining}
{self.team_batting} ({self.current_score}/{self.wickets_down}) vs {self.team_bowling}
Strike: {self.strike_batter} {self.strike_batter_runs}({self.strike_batter_balls})
Non-strike: {self.non_strike_batter} {self.non_strike_batter_runs}({self.non_strike_batter_balls})
Bowlers used: {', '.join([f"{b}: {o}o" for b, o in self.bowlers_used.items()])}
Current bowler: {self.current_bowler}
Pitch: {self.pitch_condition} | Dew: {self.dew_factor*100:.0f}% | Venue: {self.venue}
Target: {self.target} | RRR: {self.required_run_rate:.2f}
Impact Player: {'Yes' if self.impact_player_available else 'No'} | Timeouts: {self.timeouts_left}
"""

SAMPLE_MATCH_STATE = MatchState(
    innings=2, over=15, ball=3,
    team_batting="CSK", team_bowling="RCB",
    current_score=98, wickets_down=4,
    strike_batter="Jadeja", strike_batter_runs=28, strike_batter_balls=22,
    non_strike_batter="Moeen Ali", non_strike_batter_runs=18, non_strike_batter_balls=15,
    current_bowler="Siraj",
    bowlers_used={"Siraj": 3.0, "Hazelwood": 2.0, "Starc": 1.5, "Rabada": 3.0},
    pitch_condition="turning", dew_factor=0.7, venue="Wankhede",
    target=175, balls_remaining=30, required_run_rate=15.4,
    impact_player_available=True, timeouts_left=1
)
