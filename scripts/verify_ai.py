from ai_insight import analyze_news_for_ideas
import os
import json

# Mock news data so we don't depend on network/news_fetcher for this test
mock_news = [
    {'title': 'Critical SQL Injection in Popular VPN', 'summary': 'A SQLi vulnerability was found in... allows RCE...', 'link': 'http://vpn-vuln.com'},
    {'title': 'New Ransomware Group Targets Hospitals', 'summary': 'The group uses phishing... double extortion...', 'link': 'http://bad-hospital.com'},
    {'title': 'Zero-Day in Windows Kernel', 'summary': 'Privilege escalation via... POC available...', 'link': 'http://win-kernel.com'}
]

print("Testing AI Insight (JSON Mode)...")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_key_here":
    print("WARNING: GEMINI_API_KEY is missing or default. This test will likely show an error.")

insight = analyze_news_for_ideas(mock_news)
print("\n--- AI Response ---")

if isinstance(insight, list):
    print(f"Success! Received a list of {len(insight)} items.")
    print(json.dumps(insight, indent=2))
else:
    print("Error: Did not receive a list.")
    print(insight)

print("-------------------")
