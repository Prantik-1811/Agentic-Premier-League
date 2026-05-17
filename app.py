import streamlit as st
import json as _json
from dotenv import load_dotenv
load_dotenv()

from cricket_data import MatchState
from orchestrator import CaptainCoolOrchestrator
from tools.cricket_api import calculate_win_probability, fetch_live_match_state

st.set_page_config(page_title="Captain Cool 🏏", page_icon="🏏", layout="wide")
st.title("🏏 Captain Cool — Multi-Agent IPL Strategist")
st.caption("Powered by Google Gemini 2.5 Pro · 4 Agents · Real Cricket Data")

with st.sidebar:
    st.header("📋 Match State")
    cricbuzz_url = st.text_input("🔗 Cricbuzz URL (auto-fills form)", placeholder="https://www.cricbuzz.com/live-cricket-scores/...")
    if cricbuzz_url and st.button("Fetch Live State"):
        with st.spinner("Scraping Cricbuzz..."):
            live = fetch_live_match_state(cricbuzz_url)
            if live.get("scraped"):
                st.success("Fetched!")
                st.json(live)
            else:
                st.error(f"Failed: {live.get('error')}")
    st.divider()
    innings  = st.radio("Innings", [1, 2], horizontal=True)
    over     = st.slider("Over", 0, 19, 15)
    ball     = st.slider("Ball", 0, 5, 3)
    team_bat = st.text_input("Batting Team", "CSK")
    team_bowl= st.text_input("Bowling Team", "RCB")
    score    = st.number_input("Score", 0, 300, 98)
    wickets  = st.slider("Wickets Down", 0, 9, 4)
    st.subheader("Batters")
    strike_b = st.text_input("Strike Batter", "Jadeja")
    strike_r = st.number_input("Runs", 0, 200, 28, key="sr")
    strike_bl= st.number_input("Balls", 0, 200, 22, key="sb")
    non_b    = st.text_input("Non-Strike Batter", "Moeen Ali")
    non_r    = st.number_input("Runs", 0, 200, 18, key="nr")
    non_bl   = st.number_input("Balls", 0, 200, 15, key="nb")
    st.subheader("Bowling")
    curr_bowl= st.text_input("Current Bowler", "Siraj")
    bowlers_raw = st.text_area("Bowlers Used (JSON)", '{"Siraj":3.0,"Hazelwood":2.0,"Starc":1.5,"Rabada":3.0}')
    st.subheader("Conditions")
    pitch    = st.selectbox("Pitch", ["turning","flat","two-paced","seaming"])
    dew      = st.slider("Dew Factor %", 0, 100, 70) / 100
    venue    = st.text_input("Venue", "Wankhede")
    target   = st.number_input("Target", 0, 300, 175)
    balls_rem= st.number_input("Balls Remaining", 0, 120, 30)
    rrr      = st.number_input("Required Run Rate", 0.0, 36.0, 15.4)
    impact   = st.checkbox("Impact Player Available", True)
    timeouts = st.slider("Timeouts Left", 0, 2, 1)
    go       = st.button("🧠 Make Captain's Call", type="primary", use_container_width=True)

if go:
    try:
        bowlers_dict = _json.loads(bowlers_raw)
    except Exception:
        bowlers_dict = {"Siraj": 3.0, "Hazelwood": 2.0}

    match_state = MatchState(
        innings=innings, over=over, ball=ball,
        team_batting=team_bat, team_bowling=team_bowl,
        current_score=score, wickets_down=wickets,
        strike_batter=strike_b, strike_batter_runs=strike_r, strike_batter_balls=strike_bl,
        non_strike_batter=non_b, non_strike_batter_runs=non_r, non_strike_batter_balls=non_bl,
        current_bowler=curr_bowl, bowlers_used=bowlers_dict,
        pitch_condition=pitch, dew_factor=dew, venue=venue,
        target=target, balls_remaining=balls_rem, required_run_rate=rrr,
        impact_player_available=impact, timeouts_left=timeouts
    )

    orch = CaptainCoolOrchestrator()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🤖 Agent Debate")
        with st.status("Running multi-agent debate...", expanded=True) as status:
            steps_done = []
            def on_step(label):
                steps_done.append(label)
                status.update(label=f"Running: {label}...")

            result = orch.make_decision(match_state, on_step=on_step)
            status.update(label="✅ Decision ready!", state="complete")

        with st.expander("📊 Stats Analyst", expanded=False):
            st.markdown(result["stats"]["analysis"])
            if result["stats"].get("tool_data"):
                st.json(result["stats"]["tool_data"])

        with st.expander("🎯 Strategist — Initial Proposal", expanded=False):
            st.markdown(result["proposal"]["proposal"])

        with st.expander("🔴 Devil's Advocate — Challenge", expanded=True):
            st.markdown(result["challenge"]["challenge"])

        with st.expander("✅ Strategist — Final Decision", expanded=True):
            st.markdown(result["defense"]["defense"])

    with col2:
        st.subheader("🏆 Captain's Call")
        wp = calculate_win_probability(team_bat, score, wickets, balls_rem, target, pitch, dew)
        st.metric("Win Probability",     wp["win_probability_pct"])
        st.metric("Decision Confidence", f"{result['confidence']}%")
        st.metric("Resources Remaining", f"{wp.get('resource_remaining_pct','?')}%")
        st.metric("Expected Score From Here", wp.get("expected_score_from_here","?"))
        st.divider()
        st.subheader("📺 Commentary")
        st.markdown(result["commentary"]["commentary"])
