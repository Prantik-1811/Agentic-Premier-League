import os, requests, math
from bs4 import BeautifulSoup
from functools import lru_cache

CRICAPI_KEY   = os.getenv("CRICAPI_KEY")
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

# TOOL 1 — Live match scraper
def fetch_live_match_state(cricbuzz_url: str) -> dict:
    proxy = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={cricbuzz_url}"
    try:
        resp = requests.get(proxy, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        score_tag = soup.find("div", class_="cb-min-bat-rw")
        raw = score_tag.get_text(strip=True) if score_tag else "0/0 (0.0 Ov)"
        score_part, over_part = raw.split("(")
        runs, wickets = score_part.strip().split("/")
        over_str = over_part.replace("Ov)", "").strip()
        over, ball = over_str.split(".")
        crr_tag = soup.find("div", class_="cb-min-run-rr")
        crr_text = crr_tag.get_text(strip=True) if crr_tag else "CRR: 0 RRR: 0"
        crr = float(crr_text.split("CRR:")[1].split()[0]) if "CRR:" in crr_text else 0.0
        rrr = float(crr_text.split("RRR:")[1].split()[0]) if "RRR:" in crr_text else 0.0
        balls_remaining = (20 - int(over)) * 6 - int(ball)
        return {
            "source": cricbuzz_url, "current_score": int(runs),
            "wickets_down": int(wickets), "over": int(over), "ball": int(ball),
            "balls_remaining": balls_remaining, "current_run_rate": crr,
            "required_run_rate": rrr, "scraped": True
        }
    except Exception as e:
        return {"error": str(e), "scraped": False}

# TOOL 2 — Win probability (DLS-style resource model)
def calculate_win_probability(batting_team, score, wickets, balls_remaining, target, pitch_condition="flat", dew_factor=0.0) -> dict:
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
