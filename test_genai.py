import os
from google import genai
from google.genai import types

def get_venue_weather(venue: str) -> dict:
    """Gets the weather for a given venue in India."""
    return {"venue": venue, "weather": "Sunny", "dew_risk": "low"}

def run_test():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="What is the weather like in Wankhede?",
        config=types.GenerateContentConfig(
            tools=[get_venue_weather]
        )
    )
    print(response.text)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_test()
