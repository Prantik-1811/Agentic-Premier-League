from bs4 import BeautifulSoup
import re

with open("cricbuzz.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

crr_span = soup.find(string=re.compile(r"CRR:"))
if crr_span:
    container = crr_span.parent.parent.parent
    match = re.search(r"([A-Za-z]+)(\d+)", container.get_text())
    if match:
        batting_team = match.group(1)
        print("Batting team:", batting_team)

title = soup.find("title")
if title:
    title_text = title.get_text()
    # e.g., "Cricket commentary | PBKS vs RCB, 61st Match, IPL 2026"
    m = re.search(r"\|\s*([A-Za-z]+)\s*vs\s*([A-Za-z]+)", title_text)
    if m:
        t1, t2 = m.group(1), m.group(2)
        print("T1:", t1, "T2:", t2)

# Extract batters
batters = soup.find_all("div", class_=re.compile("scorecard-bat-grid"))
strike_batter = None
non_strike_batter = None
current_bowler = None

for b in batters:
    text = b.get_text(separator="|")
    if "Batter" in text or "Bowler" in text or "Key Stats" in text:
        continue
    parts = [p.strip() for p in text.split("|") if p.strip()]
    if not parts: continue
    
    # Check if it's a batter or bowler based on previous headers?
    # Actually, batters have 6 parts usually, bowlers have 5 or 6 but let's check href
    a_tag = b.find("a")
    if a_tag and "profiles" in a_tag.get("href", ""):
        name = a_tag.get_text(strip=True)
        is_striker = "*" in b.get_text()
        name = name.replace("*", "").strip()
        
        # Next divs are stats
        stats = [d.get_text(strip=True) for d in b.find_all("div", recursive=False)[1:]]
        # In a generic way, let's just use the `parts`
        # parts for batter: Name, '*', R, B, 4s, 6s, SR
        # part[0] is Name
        
        # We can distinguish batter and bowler by checking if 'scorecard-bat-grid' is for batter.
        # Wait, they all have 'scorecard-bat-grid'.
        # But we can look at the parent to see if it's batting or bowling.
        print("Found profile:", name, "Parts:", parts)

