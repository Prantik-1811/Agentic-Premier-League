import os, requests, math, re
from bs4 import BeautifulSoup
from functools import lru_cache

CRICAPI_KEY   = os.getenv("CRICAPI_KEY")
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

# TOOL 1 — Live match scraper
def fetch_live_match_state(cricbuzz_url: str) -> dict:
    """
    Scrapes the live Cricbuzz match (Commentary & Scorecard pages) via ScraperAPI.
    Merges both to get bulletproof player squads, remaining bowler overs, and venue data.
    """
    proxy_comm = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={cricbuzz_url}&render=false"
    scorecard_url = cricbuzz_url.replace("live-cricket-scores", "live-cricket-scorecard")
    proxy_card = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={scorecard_url}&render=false"

    try:
        # 1. Fetch Commentary Page
        resp_comm = requests.get(proxy_comm, timeout=20)
        resp_comm.raise_for_status()
        comm_soup = BeautifulSoup(resp_comm.text, "html.parser")

        # 2. Fetch Scorecard Page
        resp_card = requests.get(proxy_card, timeout=20)
        resp_card.raise_for_status()
        card_soup = BeautifulSoup(resp_card.text, "html.parser")

        # ── Innings number ────────────────────────────────────────────────────
        innings = 1
        batting_grids = card_soup.find_all("div", class_=re.compile("scorecard-bat-grid"))
        bat_header_count = sum(1 for tag in batting_grids if "Batter" in tag.get_text())
        if bat_header_count >= 2:
            innings = 2
        else:
            # Fallback to commentary text check
            full_text = comm_soup.get_text(" ").lower()
            if any(k in full_text for k in ["req:", "rrr:", "target:", "required run rate"]):
                innings = 2

        # ── Team names ────────────────────────────────────────────────────────
        team_tags = comm_soup.find_all("div", class_="cb-nav-subhdr")
        team_batting, team_bowling = "", ""
        if team_tags:
            raw = team_tags[0].get_text(" ", strip=True)
            parts = [p.strip() for p in raw.split("vs")]
            if len(parts) == 2:
                team_batting = parts[0].strip()
                team_bowling = parts[1].strip()

        # Fallback: extract from title
        if not team_batting:
            title = comm_soup.find("title")
            if title:
                t = title.get_text()
                if " vs " in t:
                    teams = t.split(" vs ")
                    team_batting = teams[0].strip().split()[-1]
                    team_bowling = teams[1].strip().split()[0]

        # Clean team names from punctuation, commas, active suffixes
        if team_batting:
            team_batting = re.split(r'\(|\*|innings|,', team_batting, flags=re.I)[0].strip()
        if team_bowling:
            team_bowling = re.split(r'\(|\*|innings|,', team_bowling, flags=re.I)[0].strip()
                    
        current_score, wickets_down, over, ball = 0, 0, 0, 0
        crr, rrr = 0.0, 0.0

        # Try new React-based structure first
        crr_span = comm_soup.find(string=re.compile(r"CRR:"))
        if crr_span and crr_span.parent and crr_span.parent.parent and crr_span.parent.parent.parent:
            container_text = crr_span.parent.parent.parent.get_text()
            match = re.search(r"(\d+)[-/](\d+)\(([\d\.]+)\).*CRR:\s*([\d\.]+)", container_text)
            if match:
                current_score, wickets_down = int(match.group(1)), int(match.group(2))
                overs_str = match.group(3)
                if "." in overs_str:
                    over, ball = map(int, overs_str.split("."))
                else:
                    over, ball = int(overs_str), 0
                crr = float(match.group(4))
                
                rrr_match = re.search(r"REQ:\s*([\d\.]+)", container_text)
                if rrr_match: rrr = float(rrr_match.group(1))

        if current_score == 0:
            # Fallback for old design
            score_tag = comm_soup.find("div", class_="cb-min-bat-rw")
            if score_tag:
                raw_score = score_tag.get_text(strip=True)
                try:
                    score_part, over_part = raw_score.split("(")
                    runs_str, wkts_str = score_part.strip().split("/")
                    current_score  = int(runs_str.strip())
                    wickets_down   = int(wkts_str.strip())
                    over_str       = over_part.replace("Ov)", "").replace("Ov ", "").strip()
                    if "." in over_str:
                        over, ball = map(int, over_str.split("."))
                    else:
                        over = int(over_str)
                except Exception:
                    pass

        balls_bowled    = over * 6 + ball
        balls_remaining = 120 - balls_bowled

        if crr == 0.0:
            crr_tag = comm_soup.find("div", class_="cb-min-run-rr")
            if crr_tag:
                crr_text = crr_tag.get_text(strip=True)
                if "CRR:" in crr_text:
                    try: crr = float(crr_text.split("CRR:")[1].split()[0])
                    except: pass
                if "RRR:" in crr_text:
                    try: rrr = float(crr_text.split("RRR:")[1].split()[0])
                    except: pass

        if crr == 0.0 and balls_bowled > 0:
            crr = round((current_score / balls_bowled) * 6, 2)

        # ── Target (innings 2 only) ───────────────────────────────────────────
        target = None
        if innings == 2:
            totals = []
            for tag in card_soup.find_all(string="Total"):
                parent = tag.parent.parent
                if parent:
                    text = parent.get_text("|", strip=True)
                    parts = text.split("|")
                    if len(parts) >= 2:
                        score_str = parts[1]
                        if "-" in score_str:
                            runs_str = score_str.split("-")[0].strip()
                            if runs_str.isdigit():
                                totals.append(int(runs_str))
                        elif "/" in score_str:
                            runs_str = score_str.split("/")[0].strip()
                            if runs_str.isdigit():
                                totals.append(int(runs_str))
            if totals:
                target = totals[0] + 1

            if not target:
                target_tag = comm_soup.find("div", class_="cb-min-inf")
                if target_tag:
                    t_text = target_tag.get_text(strip=True)
                    match = re.search(r"target[:\s]+(\d+)", t_text, re.IGNORECASE)
                    if match:
                        target = int(match.group(1))
            if not target:
                full_text = comm_soup.get_text(" ")
                match = re.search(r"[Tt]arget[:\s]+(\d+)", full_text)
                if match:
                    target = int(match.group(1))

        if innings == 1:
            rrr = 0.0

        # ── Batter details ────────────────────────────────────────────────────
        strike_batter, strike_runs, strike_balls   = "", 0, 0
        non_strike_batter, non_runs, non_balls     = "", 0, 0
        current_bowler = ""

        # Parse React Player Grids First
        profiles = []
        for b in comm_soup.find_all("div", class_=re.compile("scorecard-bat-grid")):
            text = b.get_text(separator="|")
            if "Batter" in text or "Bowler" in text or "Key Stats" in text: continue
            parts = [p.strip() for p in text.split("|") if p.strip()]
            if parts and b.find("a") and "profiles" in b.find("a").get("href", ""):
                profiles.append(parts)
                
        if profiles:
            if len(profiles) >= 2:
                p1, p2 = profiles[0], profiles[1]
                if len(p1) >= 3 and p1[1] == "*":
                    strike_batter = p1[0]
                    try: strike_runs = int(p1[2])
                    except: pass
                    try: strike_balls = int(p1[3])
                    except: pass
                    
                    non_strike_batter = p2[0]
                    try: non_runs = int(p2[1])
                    except: pass
                    try: non_balls = int(p2[2])
                    except: pass
                elif len(p2) >= 3 and p2[1] == "*":
                    strike_batter = p2[0]
                    try: strike_runs = int(p2[2])
                    except: pass
                    try: strike_balls = int(p2[3])
                    except: pass
                    
                    non_strike_batter = p1[0]
                    try: non_runs = int(p1[1])
                    except: pass
                    try: non_balls = int(p1[2])
                    except: pass
                else:
                    strike_batter = p1[0]
                    try: strike_runs = int(p1[1])
                    except: pass
                    try: strike_balls = int(p1[2])
                    except: pass
                    
                    non_strike_batter = p2[0]
                    try: non_runs = int(p2[1])
                    except: pass
                    try: non_balls = int(p2[2])
                    except: pass

            for p in profiles[2:]:
                if len(p) >= 2 and p[1] == "*":
                    current_bowler = p[0]
                    break
            if not current_bowler and len(profiles) >= 3:
                current_bowler = profiles[2][0]
                
        else:
            # Fallback to Old HTML structure
            batter_rows = comm_soup.find_all("div", class_="cb-min-itm-rw")
            batters_found = []
            for row in batter_rows:
                cols = row.find_all("div")
                if len(cols) >= 3:
                    name = cols[0].get_text(strip=True)
                    runs_text  = cols[1].get_text(strip=True)
                    balls_text = cols[2].get_text(strip=True)
                    if name and runs_text.isdigit():
                        batters_found.append({
                            "name": name,
                            "runs": int(runs_text),
                            "balls": int(balls_text) if balls_text.isdigit() else 0
                        })
            if len(batters_found) >= 1:
                strike_batter = batters_found[0]["name"]
                strike_runs   = batters_found[0]["runs"]
                strike_balls  = batters_found[0]["balls"]
            if len(batters_found) >= 2:
                non_strike_batter = batters_found[1]["name"]
                non_runs          = batters_found[1]["runs"]
                non_balls         = batters_found[1]["balls"]

        # ── 3. Parse Venue from Scorecard Page ──────────────────────────────────
        venue = ""
        venue_tag = card_soup.find(string=re.compile(r"Venue:"))
        if venue_tag and venue_tag.parent:
            sibling = venue_tag.parent.find_next_sibling("a")
            if sibling:
                venue = sibling.get_text(strip=True)
        if not venue:
            # Fallback to commentary page venue extraction
            venue_tag = comm_soup.find("a", class_="cb-nav-tags")
            if venue_tag:
                venue = venue_tag.get_text(strip=True)
            if not venue:
                full_text = comm_soup.get_text(" ")
                match = re.search(r"(?:at|venue)[:\s]+([A-Z][^\n,]{5,40})", full_text)
                if match:
                    venue = match.group(1).strip()

        # ── 4. Parse Bowlers and Squads from Scorecard Page ──────────────────────
        bowlers_used = {}
        for row in card_soup.find_all("div", class_=re.compile("scorecard-bowl-grid")):
            text = row.get_text("|", strip=True)
            if "Bowler" in text: continue
            parts = [p.strip() for p in text.split("|") if p.strip()]
            if len(parts) >= 2:
                name = parts[0]
                overs_b = parts[1]
                try:
                    bowlers_used[name] = float(overs_b)
                except ValueError:
                    bowlers_used[name] = 0.0

        # Parse squads to get all potential bowlers from playing XI
        squads = {}
        squad_headers = card_soup.find_all("div", string="Players")
        for sh in squad_headers:
            gg = sh.parent.parent.parent
            if gg:
                gg_text = gg.get_text("|", strip=True)
                parts = [p.strip() for p in gg_text.split("|") if p.strip()]
                if parts:
                    team_name = parts[0]
                    playing_xi = []
                    bench = []
                    current_list = playing_xi
                    for p in parts[2:]:
                        if p == "Players": continue
                        if p == "Bench":
                            current_list = bench
                            continue
                        if p == "Support Staff":
                            break
                        if p != ",":
                            clean_name = p.split("(")[0].strip().replace("*", "")
                            if clean_name:
                                current_list.append(clean_name)
                    squads[team_name] = {
                        "playing_xi": playing_xi,
                        "bench": bench
                    }

        # Find the bowling team's full name from squads matching team_bowling
        bowling_team_full = ""
        short_mapping = {
            "royal challengers bengaluru": "RCB",
            "royal challengers bangalore": "RCB",
            "punjab kings": "PBKS",
            "chennai super kings": "CSK",
            "mumbai indians": "MI",
            "kolkata knight riders": "KKR",
            "rajasthan royals": "RR",
            "delhi capitals": "DC",
            "sunrisers hyderabad": "SRH",
            "gujarat titans": "GT",
            "lucknow super giants": "LSG"
        }

        for full_t in squads.keys():
            cleaned_full = full_t.lower().strip()
            match_found = False
            for k, v in short_mapping.items():
                if k in cleaned_full and v == team_bowling.upper():
                    match_found = True
                    break
            if match_found or team_bowling.lower() in cleaned_full:
                bowling_team_full = full_t
                break

        # If we successfully found the bowling team's squad, filter and add missing playing XI members
        if bowling_team_full and bowling_team_full in squads:
            allowed_players = set(squads[bowling_team_full]["playing_xi"] + squads[bowling_team_full].get("bench", []))
            # Clean and filter bowlers_used
            bowlers_used = {name: overs for name, overs in bowlers_used.items() if name in allowed_players}
            
            playing_xi = squads[bowling_team_full]["playing_xi"]
            for player in playing_xi:
                if player not in bowlers_used:
                    bowlers_used[player] = 0.0

        # Set current bowler if not set
        if not current_bowler and bowlers_used:
            current_bowler = list(bowlers_used.keys())[0]

        # ── Pitch condition (default flat, let user adjust) ───────────────────
        pitch_condition = "flat"

        # ── Dew factor: estimate from venue + time ────────────────────────────
        coastal_venues = ["wankhede", "eden", "chepauk", "rajiv gandhi", "chinnaswamy"]
        dew_factor = 0.6 if any(v in venue.lower() for v in coastal_venues) else 0.3

        return {
            # Meta
            "source":   cricbuzz_url,
            "scraped":  True,
            "innings":  innings,

            # Teams
            "team_batting": team_batting,
            "team_bowling": team_bowling,

            # Score
            "current_score":  current_score,
            "wickets_down":   wickets_down,
            "over":           over,
            "ball":           ball,
            "balls_remaining": balls_remaining,
            "current_run_rate":  crr,
            "required_run_rate": rrr,

            # Target — None if innings 1
            "target": target,

            # Batters
            "strike_batter":       strike_batter,
            "strike_batter_runs":  strike_runs,
            "strike_batter_balls": strike_balls,
            "non_strike_batter":       non_strike_batter,
            "non_strike_batter_runs":  non_runs,
            "non_strike_batter_balls": non_balls,

            # Bowlers
            "current_bowler": current_bowler,
            "bowlers_used":   bowlers_used,

            # Conditions
            "venue":           venue,
            "pitch_condition": pitch_condition,
            "dew_factor":      dew_factor,

            # Defaults
            "impact_player_available": True,
            "timeouts_left": 1,
        }

    except Exception as e:
        return {"error": str(e), "scraped": False, "source": cricbuzz_url}

# TOOL 2 — Win probability (DLS-style resource model)
def calculate_win_probability(batting_team: str, score: int, wickets: int, balls_remaining: int, target: int, pitch_condition: str = "flat", dew_factor: float = 0.0) -> dict:
    RESOURCE_TABLE = {
        (120,0):100.0,(120,1):93.4,(120,2):85.1,(120,3):74.9,(120,4):62.7,(120,5):49.0,(120,6):34.9,(120,7):22.0,(120,8):11.9,(120,9):4.7,(120,10):0.0,
        (90,0):85.1,(90,1):79.4,(90,2):72.4,(90,3):63.5,(90,4):52.6,(90,5):40.5,(90,6):28.3,(90,7):17.3,(90,8):9.0,(90,9):3.3,(90,10):0.0,
        (60,0):66.5,(60,1):61.8,(60,2):55.9,(60,3):48.4,(60,4):39.4,(60,5):29.8,(60,6):20.4,(60,7):12.1,(60,8):6.0,(60,9):2.1,(60,10):0.0,
        (30,0):40.6,(30,1):37.4,(30,2):33.2,(30,3):28.0,(30,4):22.0,(30,5):16.0,(30,6):10.5,(30,7):5.8,(30,8):2.6,(30,9):0.8,(30,10):0.0,
        (12,0):20.1,(12,1):18.2,(12,2):15.7,(12,3):12.7,(12,4):9.4,(12,5):6.4,(12,6):3.9,(12,7):1.9,(12,8):0.7,(12,9):0.2,(12,10):0.0,
        (6,0):11.0,(6,1):9.8,(6,2):8.2,(6,3):6.3,(6,4):4.4,(6,5):2.7,(6,6):1.5,(6,7):0.6,(6,8):0.2,(6,9):0.0,(6,10):0.0,
    }
    def interpolate(balls, wkts):
        checkpoints = [6,12,30,60,90,120]
        lower = max([c for c in checkpoints if c <= balls], default=6)
        upper = min([c for c in checkpoints if c >= balls], default=120)
        r_low = RESOURCE_TABLE.get((lower, min(wkts,10)), 0.0)
        r_up  = RESOURCE_TABLE.get((upper, min(wkts,10)), 0.0)
        if upper == lower: return r_low
        return r_low + (balls - lower) / (upper - lower) * (r_up - r_low)

    runs_needed = target - score
    if runs_needed <= 0: return {"win_probability": 1.0, "win_probability_pct": "100%", "runs_needed": 0}
    if balls_remaining <= 0 or wickets >= 10: return {"win_probability": 0.0, "win_probability_pct": "0%", "runs_needed": runs_needed}

    resource_pct = interpolate(balls_remaining, wickets)
    expected = (resource_pct / 100) * 160
    pitch_mult = {"flat":1.10,"two-paced":1.00,"turning":0.88,"seaming":0.85}.get(pitch_condition, 1.0)
    dew_boost = 1 + (dew_factor * 0.08)
    adjusted = expected * pitch_mult * dew_boost
    diff = adjusted - runs_needed
    win_prob = round(max(0.03, min(0.97, 1 / (1 + math.exp(-diff / 15)))), 3)
    return {
        "win_probability": win_prob,
        "win_probability_pct": f"{win_prob*100:.1f}%",
        "runs_needed": runs_needed,
        "balls_remaining": balls_remaining,
        "resource_remaining_pct": round(resource_pct, 1),
        "expected_score_from_here": round(adjusted, 1),
        "model": "dls_heuristic_v1"
    }

# TOOL 3 — Player stats (CricAPI + embedded fallback)
FALLBACK_STATS = {
    "jadeja":     {"name":"Ravindra Jadeja","team":"CSK","batting":{"avg":29.4,"sr":151.2},"bowling":{"economy":7.8,"avg":28.1},"vs_pace_death":{"avg":18.0,"sr":145.0},"vs_spin_death":{"avg":31.0,"sr":165.0}},
    "siraj":      {"name":"Mohammed Siraj","team":"RCB","bowling":{"economy":9.1,"avg":31.4},"death_economy":10.2,"4th_spell_economy":9.2},
    "hazelwood":  {"name":"Josh Hazelwood","team":"RCB","bowling":{"economy":7.9,"avg":22.1},"death_economy":8.4},
    "starc":      {"name":"Mitchell Starc","team":"RCB","bowling":{"economy":8.6,"avg":25.3},"yorker_success_rate":0.72},
    "moeen ali":  {"name":"Moeen Ali","team":"CSK","batting":{"avg":22.1,"sr":158.4},"vs_spin":{"avg":19.0,"sr":148.0}},
    "dhoni":      {"name":"MS Dhoni","team":"CSK","batting":{"avg":38.5,"sr":182.1},"finishing_sr":191.3},
    "kohli":      {"name":"Virat Kohli","team":"RCB","batting":{"avg":44.2,"sr":131.8}},
    "rohit":      {"name":"Rohit Sharma","team":"MI","batting":{"avg":31.2,"sr":139.5}},
}

@lru_cache(maxsize=64)
def get_player_stats(player_name: str) -> dict:
    try:
        search = requests.get(f"https://api.cricapi.com/v1/players?apikey={CRICAPI_KEY}&search={player_name}", timeout=8)
        data = search.json()
        if data.get("status") == "success" and data.get("data"):
            pid = data["data"][0]["id"]
            stats = requests.get(f"https://api.cricapi.com/v1/players_info?apikey={CRICAPI_KEY}&id={pid}", timeout=8).json()
            if stats.get("status") == "success":
                return {"source":"cricapi","player":stats["data"],"fallback":False}
    except Exception:
        pass
    key = player_name.lower().strip()
    for k, v in FALLBACK_STATS.items():
        if k in key or key in k:
            return {"source":"embedded_ipl2024","player":v,"fallback":True}
    return {"source":"not_found","player":{"name":player_name},"fallback":True}

# TOOL 4 — Head-to-head
H2H_DB = {
    ("jadeja","siraj"):       {"balls":18,"runs":24,"dismissals":2,"avg":12.0,"sr":133.3},
    ("jadeja","hazelwood"):   {"balls":12,"runs":19,"dismissals":1,"avg":19.0,"sr":158.3},
    ("jadeja","starc"):       {"balls":9, "runs":16,"dismissals":0,"avg":None,"sr":177.8},
    ("moeen ali","siraj"):    {"balls":14,"runs":21,"dismissals":1,"avg":21.0,"sr":150.0},
    ("moeen ali","hazelwood"):{"balls":8, "runs":10,"dismissals":2,"avg":5.0, "sr":125.0},
    ("dhoni","siraj"):        {"balls":22,"runs":41,"dismissals":1,"avg":41.0,"sr":186.4},
    ("kohli","jadeja"):       {"balls":45,"runs":52,"dismissals":3,"avg":17.3,"sr":115.6},
    ("rohit","bumrah"):       {"balls":31,"runs":38,"dismissals":2,"avg":19.0,"sr":122.6},
}

def get_head_to_head(batter: str, bowler: str) -> dict:
    b, bow = batter.lower().strip(), bowler.lower().strip()
    result = H2H_DB.get((b, bow)) or H2H_DB.get((bow, b))
    if result:
        avg = result["avg"]
        sr  = result["sr"]
        summary = (
            f"{bowler} dominates — {batter} averages only {avg}"
            if avg and avg < 20 else
            f"{batter} has the edge — SR of {sr} against {bowler}"
            if sr > 155 else
            f"Evenly matched — SR {sr}"
        )
        return {**result, "batter":batter, "bowler":bowler,
                "dominance_summary":summary, "source":"embedded_ipl_2020_2024"}
    return {"batter":batter,"bowler":bowler,"note":"No data found","source":"not_found"}
