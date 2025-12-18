"""
News and CVE fetcher for cybersecurity information.
Optimized for performance with better error handling and efficiency.
"""

import feedparser
import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

_executor = ThreadPoolExecutor(max_workers=5)

NEWS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://krebsonsecurity.com/feed/",
    "https://threatpost.com/feed/",
    "https://www.darkreading.com/rss.xml",
    "https://www.securityweek.com/rss",
    "https://www.infosecurity-magazine.com/rss/news/",
    "https://www.csoonline.com/index.rss",
    "https://www.zdnet.com/topic/security/rss.xml",
    "https://www.wired.com/feed/tag/security/latest/rss",
    "https://feeds.feedburner.com/SecurityFocus",
    "https://www.schneier.com/feed/",
    "https://www.theregister.com/security/headlines.atom",
    "https://www.cyberscoop.com/feed/",
    "https://www.cybersecurity-insiders.com/feed/",
    "https://www.securitymagazine.com/rss/topic/219-information-security",
    "https://www.helpnetsecurity.com/feed/",
    "https://www.securityaffairs.com/feed",
    "https://www.hackread.com/feed/",
    "https://www.securitynewspaper.com/feed/",
]

CVE_FEEDS = [
    "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml",
    "https://www.securityfocus.com/vulnerabilities/rss",
]

_HTML_TAG_PATTERN = re.compile(r'<[^<]+?>')
_HTML_ENTITY_PATTERN = re.compile(r'&(nbsp|amp|lt|gt|quot);')


def _clean_html(text: str) -> str:
    """Efficiently clean HTML from text."""
    if not text or '<' not in text:
        return text
    
    text = _HTML_TAG_PATTERN.sub('', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    return text.strip()


def _parse_feed_entry(entry, source_name: str, is_cve: bool = False) -> Optional[Dict]:
    """Parse a feed entry into a standardized format."""
    try:
        title = entry.get('title', 'Untitled')
        link = entry.get('link', '')
        
        summary = entry.get('summary') or entry.get('description') or 'No description available.'
        summary = _clean_html(summary)
        
        date_str = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                date_str = datetime(*entry.published_parsed[:6]).isoformat()
            except (ValueError, TypeError):
                pass
        
        item: Dict = {
            'title': title,
            'link': link,
            'summary': summary[:500] if len(summary) > 500 else summary,
            'source': source_name,
            'date': date_str,
            'type': 'CVE' if is_cve else 'News'
        }
        
        if is_cve:
            cve_match = re.search(r'CVE-\d{4}-\d{4,}', title + ' ' + link)
            if cve_match:
                item['cve_id'] = cve_match.group(0)
        
        return item
    except Exception as e:
        print(f"Error parsing feed entry: {e}")
        return None


def _fetch_rss_feed(feed_url: str, source_name: str, is_cve: bool = False, max_items: int = 5) -> List[Dict]:
    """Fetch items from an RSS feed."""
    items = []
    try:
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception and not isinstance(feed.bozo_exception, Exception):
            pass
        
        for entry in feed.entries[:max_items]:
            item = _parse_feed_entry(entry, source_name, is_cve)
            if item:
                items.append(item)
    except Exception as e:
        if "getaddrinfo" not in str(e) and "urlopen" not in str(e):
            print(f"Error fetching {feed_url}: {e}")
    
    return items


def _fetch_nvd_cve_recent(limit: int = 5) -> List[Dict]:
    """Fetch recent CVEs from NIST NVD API."""
    items = []
    try:
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        params = {
            'resultsPerPage': min(limit, 20),
            'pubStartDate': start_date.strftime('%Y-%m-%dT00:00:00.000'),
            'pubEndDate': end_date.strftime('%Y-%m-%dT23:59:59.999'),
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'vulnerabilities' in data:
                for vuln in data['vulnerabilities'][:limit]:
                    cve_data = vuln.get('cve', {})
                    cve_id = cve_data.get('id', 'Unknown')
                    
                    descriptions = cve_data.get('descriptions', [])
                    description = 'No description available.'
                    if descriptions:
                        for desc in descriptions:
                            if desc.get('lang') == 'en':
                                description = desc.get('value', description)
                                break
                        if description == 'No description available.':
                            description = descriptions[0].get('value', description)
                    
                    cvss_score = None
                    metrics = cve_data.get('metrics', {})
                    for metric_key in ('cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2'):
                        if metric_key in metrics and metrics[metric_key]:
                            cvss_score = metrics[metric_key][0].get('cvssData', {}).get('baseScore')
                            break
                    
                    items.append({
                        'title': f"{cve_id}: {description[:100]}",
                        'link': f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                        'summary': description[:500],
                        'source': 'NIST NVD',
                        'date': cve_data.get('published', ''),
                        'type': 'CVE',
                        'cve_id': cve_id,
                        'cvss_score': cvss_score
                    })
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NVD API: {e}")
    except Exception as e:
        print(f"Error processing NVD data: {e}")
    
    return items


def get_latest_news(limit: int = 5, include_cves: bool = True) -> List[Dict]:
    """
    Fetches the latest news from configured RSS feeds with parallel processing.
    
    Args:
        limit: Maximum number of items to return
        include_cves: Whether to include CVE information
    
    Returns:
        List of dictionaries with title, link, summary, source, type, etc.
    """
    all_items: List[Dict] = []
    
    futures = []
    for feed_url in NEWS_FEEDS:
        source_name = feed_url.split('/')[-1].replace('.xml', '').replace('.rss', '').replace('.atom', '')
        future = _executor.submit(_fetch_rss_feed, feed_url, source_name, False, 2)
        futures.append(future)
    
    for future in as_completed(futures):
        try:
            items = future.result(timeout=5)
            all_items.extend(items)
        except Exception as e:
            print(f"Error in parallel feed fetch: {e}")
    
    if include_cves:
        for feed_url in CVE_FEEDS:
            source_name = feed_url.split('/')[-1] if '/' in feed_url else 'CVE Feed'
            items = _fetch_rss_feed(feed_url, source_name, is_cve=True, max_items=2)
            all_items.extend(items)
            time.sleep(0.1)
        
        nvd_items = _fetch_nvd_cve_recent(limit=3)
        all_items.extend(nvd_items)
    
    def get_sort_key(item: Dict) -> datetime:
        date_str = item.get('date')
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        return datetime.min
    
    all_items.sort(key=get_sort_key, reverse=True)
    
    return all_items[:limit]


def get_cves_only(limit: int = 5) -> List[Dict]:
    """
    Fetches only CVE information.
    
    Args:
        limit: Maximum number of CVEs to return
    
    Returns:
        List of CVE dictionaries
    """
    cve_items: List[Dict] = []
    
    for feed_url in CVE_FEEDS:
        source_name = feed_url.split('/')[-1] if '/' in feed_url else 'CVE Feed'
        items = _fetch_rss_feed(feed_url, source_name, is_cve=True, max_items=3)
        cve_items.extend(items)
        time.sleep(0.1)
    
    nvd_items = _fetch_nvd_cve_recent(limit=limit)
    cve_items.extend(nvd_items)
    
    def get_sort_key(item: Dict) -> datetime:
        date_str = item.get('date')
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        return datetime.min
    
    cve_items.sort(key=get_sort_key, reverse=True)
    
    return cve_items[:limit]
