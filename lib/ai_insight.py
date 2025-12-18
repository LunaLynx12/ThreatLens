"""
AI-powered project idea generation using Gemini API.
"""

from google import genai
import os
import json
import time


def analyze_news_for_ideas(news_items, max_retries=2):
    """
    Uses Gemini API (google-genai) to generate project ideas based on news.
    Includes retry logic for temporary API errors.
    """
    if not os.getenv("GEMINI_API_KEY"):
        return "Error: GEMINI_API_KEY not configured in environment."

    for attempt in range(max_retries + 1):
        try:
            client = genai.Client()
            
            news_text = "\n\n".join([
                f"Article {i+1}:\nTitle: {item['title']}\nLink: {item['link']}\nSummary: {item['summary']}"
                for i, item in enumerate(news_items)
            ])
            
            prompt = f"""You are a Cybersecurity Research Mentor analyzing the latest threat landscape.

LATEST CYBERSECURITY NEWS:
{news_text}

TASK: Generate 3 UNIQUE, DIVERSE project ideas. Each idea MUST:
1. Be directly inspired by a DIFFERENT news article (use Article 1, Article 2, Article 3)
2. Address the SPECIFIC vulnerability, attack vector, or technology mentioned in that article
3. Have UNIQUE requirements tailored to that specific threat/technology
4. NOT repeat the same tech stack or tools across ideas

CRITICAL REQUIREMENTS:
- Each project must use DIFFERENT technologies/languages based on what's relevant to that specific news story
- Requirements should match the actual technology stack mentioned in the article (e.g., if article mentions Python exploits, use Python; if it mentions CVE in a web app, use web technologies)
- Make requirements SPECIFIC and DIVERSE - avoid generic lists
- Each idea should tackle a DIFFERENT aspect of cybersecurity (e.g., one on malware analysis, one on web exploitation, one on network security)

Return ONLY a valid JSON array with this exact structure:
[
    {{
        "title": "Specific project name related to Article 1's threat",
        "inspiration_link": "URL from Article 1",
        "description": "Detailed description explaining how this project addresses the specific threat from Article 1",
        "requirements": ["Specific tech/language 1", "Specific tool 2", "Specific framework 3"],
        "functionalities": ["Feature that addresses Article 1's vulnerability", "Another relevant feature"]
    }},
    {{
        "title": "Specific project name related to Article 2's threat",
        "inspiration_link": "URL from Article 2",
        "description": "Detailed description explaining how this project addresses the specific threat from Article 2",
        "requirements": ["DIFFERENT tech/language 1", "DIFFERENT tool 2", "DIFFERENT framework 3"],
        "functionalities": ["Feature that addresses Article 2's vulnerability", "Another relevant feature"]
    }},
    {{
        "title": "Specific project name related to Article 3's threat",
        "inspiration_link": "URL from Article 3",
        "description": "Detailed description explaining how this project addresses the specific threat from Article 3",
        "requirements": ["DIFFERENT tech/language 1", "DIFFERENT tool 2", "DIFFERENT framework 3"],
        "functionalities": ["Feature that addresses Article 3's vulnerability", "Another relevant feature"]
    }}
]

Ensure requirements are UNIQUE and SPECIFIC to each article's technology stack and threat type."""

            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )
            
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                text = response.text.replace('```json', '').replace('```', '').strip()
                return json.loads(text)
                
        except Exception as e:
            error_str = str(e)
            
            if "503" in error_str or "UNAVAILABLE" in error_str or "overloaded" in error_str.lower():
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                    continue
                else:
                    return "⚠️ The AI service is currently overloaded. Please try again in a few moments."
            
            elif "401" in error_str or "403" in error_str or "API key" in error_str.lower():
                return "❌ API authentication failed. Please check your GEMINI_API_KEY."
            
            elif "429" in error_str or "rate limit" in error_str.lower():
                return "⚠️ Rate limit exceeded. Please wait a moment before trying again."
            
            else:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    return f"❌ AI service error: {error_str[:200]}"
    
    return "❌ Failed to generate ideas after multiple attempts. Please try again later."
