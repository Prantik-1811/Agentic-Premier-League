# Captain Cool — Multi-Agent IPL Match Strategist

## Architecture
```
   [Match State]
        |
        v
 [Stats Analyst]
        | (Stats Data)
        v
  [Strategist]  <----->  [Devil's Advocate]
        | (Final Plan)
        v
  [Commentator]
        |
        v
    [UI Stream]
```

## Setup
```bash
pip install -r requirements.txt
# Add GEMINI_API_KEY to .env
streamlit run app.py
```

## How It Works
**Stats Analyst**: Gathers intelligence using function calling (win probability, player stats, head-to-head records). It focuses purely on numbers, establishing the ground truth for decision making.

**Strategist**: The core decision maker. Takes the intelligence from the Stats Analyst and acts like MS Dhoni—making bold, decisive tactical calls including bowler selection, field placements, and impact player usage.

**Devil's Advocate**: Challenges the Strategist's plan by actively seeking flaws and proposing counter-arguments, forcing a more robust final decision.

**Match Commentator**: Takes the final finalized tactical decision and narrates it in a TV-style, Harsha Bhogle-esque commentary to make the output engaging for the user.

## Sample Output
```
🔵 [Stats Analyst] 
- CSK win probability stands at ~45%
- Siraj economy: 8.5
- H2H: Jadeja has scored 45 runs off 35 balls against Siraj (2 dismissals)

🟡 [Strategist]
Captain's Call: Bowl Siraj. Keep mid-off up. Use the turning pitch to cramp Jadeja.

🔴 [Devil's Advocate]
Counter-argument: Siraj might go for runs if the dew factor is 0.7. Bring in Starc instead to exploit the seam.

🟢 [Strategist Defense]
Final Call: We stick with Siraj. Starc is better reserved for the 18th over. The turning pitch will help Siraj's cutters despite the dew.

📺 [Commentator]
Oh, what a masterstroke! The captain has decided to back his premier fast bowler in the death. The field is set, the crowd is buzzing. Can Siraj deliver against the dangerous Jadeja?
```
