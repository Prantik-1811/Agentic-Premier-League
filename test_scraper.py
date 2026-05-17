import os
from dotenv import load_dotenv
import requests

load_dotenv()
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
cricbuzz_url = "https://www.cricbuzz.com/live-cricket-scores/152174/rcb-vs-pbks-61st-match-indian-premier-league-2026"
proxy = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={cricbuzz_url}"

try:
    resp = requests.get(proxy, timeout=15)
    with open("cricbuzz.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
except Exception as e:
    print("Error:", e)
