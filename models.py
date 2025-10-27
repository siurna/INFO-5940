import os, requests, json

API_KEY = os.getenv("API_KEY") or input("Enter your Cornell AI Gateway key: ").strip()
BASE = "https://api.ai.it.cornell.edu/v1"

def test_route(route):
    url = f"{BASE}/{route}"
    body = {
        "model": "openai.gpt-4o-mini",
        "input": [{"role": "user", "content": "say hello"}]
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    r = requests.post(url, headers=headers, json=body)
    print(f"\n➡️  Tried {route} — status {r.status_code}")
    try:
        print(r.json())
    except:
        print(r.text)

for route in ["chat/completions", "responses"]:
    test_route(route)