from news_fetcher import get_latest_news
import sys

try:
    print("Testing news fetcher...")
    news = get_latest_news()
    print(f"Successfully fetched {len(news)} articles.")
    if news:
        print(f"Latest: {news[0]['title']}")
    else:
        print("No articles found (but no error).")
except ImportError:
    print("Error: feedparser not installed.")
except Exception as e:
    print(f"Error: {e}")
