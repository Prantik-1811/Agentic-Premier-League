import streamlit as st
import asyncio
import json
from cricket_data import MatchState
from orchestrator import captain_decision

st.set_page_config(page_title="Captain Cool", layout="wide")

st.title("🏏 Captain Cool — Multi-Agent IPL Match Strategist")

# Sidebar Form
with st.sidebar:
    st.header("Match State Input")
    
    # URL autofill mock
    url = st.text_input("Cricbuzz URL (Optional auto-fill)")
    
    innings = st.radio("Innings", [1, 2], index=1)
    over = st.slider("Over", 0, 19, 15)
    ball = st.slider("Ball", 0, 5, 3)
    team_batting = st.text_input("Batting Team", "CSK")
    team_bowling = st.text_input("Bowling Team", "RCB")
    current_score = st.number_input("Current Score", 0, 400, 98)
    wickets_down = st.slider("Wickets Down", 0, 10, 4)
    
    strike_batter = st.text_input("Strike Batter", "Jadeja")
    strike_batter_runs = st.number_input("Strike Batter Runs", 0, 200, 28)
    strike_batter_balls = st.number_input("Strike Batter Balls", 0, 100, 22)
    
    non_strike_batter = st.text_input("Non-Strike Batter", "Moeen Ali")
    non_strike_batter_runs = st.number_input("Non-Strike Batter Runs", 0, 200, 18)
    non_strike_batter_balls = st.number_input("Non-Strike Batter Balls", 0, 100, 15)
    
    current_bowler = st.text_input("Current Bowler", "Siraj")
    bowlers_used_str = st.text_area("Bowlers Used (JSON)", '{"Siraj": 3.0, "Hazelwood": 2.0, "Starc": 1.5, "Rabada": 3.0}')
    
    pitch_condition = st.selectbox("Pitch Condition", ["turning", "flat", "two-paced", "seaming"])
    dew_factor = st.slider("Dew Factor (%)", 0, 100, 70) / 100.0
    venue = st.text_input("Venue", "Wankhede")
    target = st.number_input("Target", 0, 400, 175)
    balls_remaining = st.number_input("Balls Remaining", 0, 120, 30)
    required_run_rate = st.number_input("Required Run Rate", 0.0, 36.0, 15.4)
    impact_player_available = st.checkbox("Impact Player Available", value=True)
    timeouts_left = st.slider("Timeouts Left", 0, 2, 1)
    
    analyze_btn = st.button("Generate Strategy")

# Main Panel
if analyze_btn:
    try:
        bowlers_used = json.loads(bowlers_used_str)
    except Exception:
        bowlers_used = {}
        
    match_state = MatchState(
        innings=innings, over=over, ball=ball, team_batting=team_batting, team_bowling=team_bowling,
        current_score=current_score, wickets_down=wickets_down, strike_batter=strike_batter,
        strike_batter_runs=strike_batter_runs, strike_batter_balls=strike_batter_balls,
        non_strike_batter=non_strike_batter, non_strike_batter_runs=non_strike_batter_runs,
        non_strike_batter_balls=non_strike_batter_balls, current_bowler=current_bowler,
        bowlers_used=bowlers_used, pitch_condition=pitch_condition, dew_factor=dew_factor,
        venue=venue, target=target, balls_remaining=balls_remaining, required_run_rate=required_run_rate,
        impact_player_available=impact_player_available, timeouts_left=timeouts_left
    )
    
    st.subheader("Agent Debate in Progress...")
    
    async def run_analysis():
        containers = {
            "stats_analyst": st.empty(),
            "strategist_initial": st.empty(),
            "devils_advocate": st.empty(),
            "strategist_final": st.empty(),
            "commentator": st.empty()
        }
        
        final_data = None
        
        async for result in captain_decision(match_state):
            step = result["step"]
            if step == "final_summary":
                final_data = result["content"]
                break
                
            status = result["status"]
            container = containers[step]
            
            icons = {
                "stats_analyst": "🔵 [Stats Analyst]",
                "strategist_initial": "🟡 [Strategist Initial]",
                "devils_advocate": "🔴 [Devil's Advocate]",
                "strategist_final": "🟢 [Strategist Defense]",
                "commentator": "📺 [Commentator]"
            }
            title = icons.get(step, step)
            
            if status == "running":
                with container.expander(f"{title} - Thinking...", expanded=True):
                    st.spinner("Analyzing...")
            else:
                with container.expander(f"{title} - Done", expanded=False):
                    st.write(result["content"])
        
        if final_data:
            st.markdown("---")
            st.markdown(f"""
            ### 🏏 CAPTAIN'S CALL
            **Next Bowler:** {final_data['final_decision'][:50]}...
            **Confidence:** {final_data['confidence_score']}%
            """)
            st.success(final_data['final_decision'])
            
            st.markdown("---")
            st.markdown("### 📺 Live Commentary")
            st.info(final_data['commentary'])

    asyncio.run(run_analysis())
