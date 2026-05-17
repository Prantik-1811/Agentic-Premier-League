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

# ── Session state defaults ────────────────────────────────────────────────────
DEFAULTS = {
    "innings":       2,
    "over":          15,
    "ball":          3,
    "team_batting":  "CSK",
    "team_bowling":  "RCB",
    "score":         98,
    "wickets":       4,
    "strike_b":      "Jadeja",
    "strike_r":      28,
    "strike_bl":     22,
    "non_b":         "Moeen Ali",
    "non_r":         18,
    "non_bl":        15,
    "curr_bowl":     "Siraj",
    "bowlers_raw":   '{"Siraj":3.0,"Hazelwood":2.0,"Starc":1.5,"Rabada":3.0}',
    "pitch":         "flat",
    "dew":           40,
    "venue":         "Wankhede",
    "target":        175,
    "balls_rem":     30,
    "rrr":           15.4,
    "impact":        True,
    "timeouts":      1,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Match State")

    cricbuzz_url = st.text_input(
        "🔗 Cricbuzz URL (auto-fills form)",
        placeholder="https://www.cricbuzz.com/live-cricket-scores/..."
    )

    if st.button("⬇️ Fetch Live State", use_container_width=True):
        with st.spinner("Scraping Cricbuzz..."):
            live = fetch_live_match_state(cricbuzz_url)

        if live.get("scraped"):
            st.success("✅ Fetched! Form auto-filled below.")

            # ── Map scraped data → session_state ──────────────────────────
            st.session_state["innings"]      = live.get("innings", 1)
            st.session_state["over"]         = live.get("over", 0)
            st.session_state["ball"]         = live.get("ball", 0)
            st.session_state["team_batting"] = live.get("team_batting", "")
            st.session_state["team_bowling"] = live.get("team_bowling", "")
            st.session_state["score"]        = live.get("current_score", 0)
            st.session_state["wickets"]      = live.get("wickets_down", 0)
            st.session_state["strike_b"]     = live.get("strike_batter", "")
            st.session_state["strike_r"]     = live.get("strike_batter_runs", 0)
            st.session_state["strike_bl"]    = live.get("strike_batter_balls", 0)
            st.session_state["non_b"]        = live.get("non_strike_batter", "")
            st.session_state["non_r"]        = live.get("non_strike_batter_runs", 0)
            st.session_state["non_bl"]       = live.get("non_strike_batter_balls", 0)
            st.session_state["curr_bowl"]    = live.get("current_bowler", "")
            st.session_state["venue"]        = live.get("venue", "")
            st.session_state["balls_rem"]    = live.get("balls_remaining", 30)
            st.session_state["dew"]          = int(live.get("dew_factor", 0.3) * 100)
            st.session_state["pitch"]        = live.get("pitch_condition", "flat")

            # CRR as display only; RRR only if innings 2
            crr = live.get("current_run_rate", 0.0)
            rrr = live.get("required_run_rate", 0.0)
            st.session_state["rrr"] = rrr if live.get("innings", 1) == 2 else 0.0

            # Target: only set if innings 2 and target found
            if live.get("innings", 1) == 2 and live.get("target"):
                st.session_state["target"] = live["target"]
            else:
                st.session_state["target"] = 0  # innings 1 = no target

            # Bowlers used as JSON string
            bowlers = live.get("bowlers_used", {})
            st.session_state["bowlers_raw"] = _json.dumps(bowlers) if bowlers else "{}"

            st.rerun()

        else:
            st.error(f"❌ Scrape failed: {live.get('error', 'Unknown error')}")
            st.info("Fill in the form manually below.")

    st.divider()

    # ── All form fields bound to session_state ────────────────────────────────
    innings  = st.radio("Innings", [1, 2], index=st.session_state["innings"]-1, horizontal=True, key="innings")
    over     = st.slider("Over", 0, 19, key="over")
    ball     = st.slider("Ball", 0, 5, key="ball")
    team_bat = st.text_input("Batting Team", key="team_batting")
    team_bowl= st.text_input("Bowling Team", key="team_bowling")
    score    = st.number_input("Score", 0, 300, key="score")
    wickets  = st.slider("Wickets Down", 0, 9, key="wickets")

    st.subheader("Batters")
    strike_b = st.text_input("Strike Batter", key="strike_b")
    strike_r = st.number_input("Runs", 0, 200, key="strike_r")
    strike_bl= st.number_input("Balls", 0, 200, key="strike_bl")
    non_b    = st.text_input("Non-Strike Batter", key="non_b")
    non_r    = st.number_input("Runs ", 0, 200, key="non_r")
    non_bl   = st.number_input("Balls ", 0, 200, key="non_bl")

    st.subheader("Bowling")
    curr_bowl   = st.text_input("Current Bowler", key="curr_bowl")
    bowlers_raw = st.text_area("Bowlers Used (JSON)", key="bowlers_raw")

    st.subheader("Conditions")
    pitch    = st.selectbox("Pitch", ["flat","turning","two-paced","seaming"],
                            index=["flat","turning","two-paced","seaming"].index(st.session_state["pitch"]),
                            key="pitch")
    dew      = st.slider("Dew Factor %", 0, 100, key="dew")
    venue    = st.text_input("Venue", key="venue")

    # ── Innings-aware fields ──────────────────────────────────────────────────
    st.subheader("Match Context")

    if st.session_state["innings"] == 1:
        st.info("🏏 1st Innings — no target yet. RRR not applicable.")
        target   = 0
        rrr      = 0.0
        balls_rem = st.number_input("Balls Remaining", 0, 120, key="balls_rem")
    else:
        target   = st.number_input("Target", 0, 300, key="target")
        balls_rem= st.number_input("Balls Remaining", 0, 120, key="balls_rem")
        rrr      = st.number_input("Required Run Rate", 0.0, 36.0, key="rrr")

    # CRR display (read-only, computed)
    balls_bowled = over * 6 + ball
    crr_computed = round((score / balls_bowled) * 6, 2) if balls_bowled > 0 else 0.0
    st.metric("Current Run Rate", crr_computed)

    impact   = st.checkbox("Impact Player Available", key="impact")
    timeouts = st.slider("Timeouts Left", 0, 2, key="timeouts")

    go = st.button("🧠 Make Captain's Call", type="primary", use_container_width=True)

# ── Main panel ────────────────────────────────────────────────────────────────
if go:
    try:
        bowlers_dict = _json.loads(st.session_state["bowlers_raw"])
    except Exception:
        bowlers_dict = {}

    # Build MatchState — target is None for innings 1
    match_state = MatchState(
        innings=st.session_state["innings"],
        over=st.session_state["over"],
        ball=st.session_state["ball"],
        team_batting=st.session_state["team_batting"],
        team_bowling=st.session_state["team_bowling"],
        current_score=st.session_state["score"],
        wickets_down=st.session_state["wickets"],
        strike_batter=st.session_state["strike_b"],
        strike_batter_runs=st.session_state["strike_r"],
        strike_batter_balls=st.session_state["strike_bl"],
        non_strike_batter=st.session_state["non_b"],
        non_strike_batter_runs=st.session_state["non_r"],
        non_strike_batter_balls=st.session_state["non_bl"],
        current_bowler=st.session_state["curr_bowl"],
        bowlers_used=bowlers_dict,
        pitch_condition=st.session_state["pitch"],
        dew_factor=st.session_state["dew"] / 100,
        venue=st.session_state["venue"],
        target=st.session_state["target"] if st.session_state["innings"] == 2 else None,
        balls_remaining=st.session_state["balls_rem"],
        required_run_rate=st.session_state.get("rrr", 0.0) if st.session_state["innings"] == 2 else 0.0,
        impact_player_available=st.session_state["impact"],
        timeouts_left=st.session_state["timeouts"],
    )

    orch = CaptainCoolOrchestrator()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🤖 Agent Debate")
        with st.status("Running multi-agent debate...", expanded=True) as status:
            def on_step(label):
                status.update(label=f"⏳ Running: {label}...")
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

        if st.session_state["innings"] == 2 and st.session_state["target"]:
            wp = calculate_win_probability(
                st.session_state["team_batting"],
                st.session_state["score"],
                st.session_state["wickets"],
                st.session_state["balls_rem"],
                st.session_state["target"],
                st.session_state["pitch"],
                st.session_state["dew"] / 100
            )
            st.metric("Win Probability",          wp["win_probability_pct"])
            st.metric("Resources Remaining",      f"{wp.get('resource_remaining_pct','?')}%")
            st.metric("Expected Score From Here", wp.get("expected_score_from_here","?"))
        else:
            # Innings 1 — show projected total instead
            balls_left = st.session_state["balls_rem"]
            crr_now = crr_computed
            projected = st.session_state["score"] + round((balls_left / 6) * crr_now)
            st.metric("Current Run Rate",   crr_computed)
            st.metric("Projected Total",    projected)
            st.metric("Balls Remaining",    balls_left)

        st.metric("Decision Confidence", f"{result['confidence']}%")
        st.divider()
        st.subheader("📺 Commentary")
        st.markdown(result["commentary"]["commentary"])
