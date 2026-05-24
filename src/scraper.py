"""Article content extractor using trafilatura."""

import logging
import time
from typing import Optional

import trafilatura
import requests

logger = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({'User-Agent': 'CareInfoBot/1.0 (research; +https://github.com)'})

SKIP_DOMAINS = {'twitter.com', 'x.com', 't.co', 'facebook.com', 'instagram.com', 'youtube.com'}


def _should_skip(url: str) -> bool:
    from urllib.parse import urlparse
    try:
        domain = urlparse(url).netloc.lower().lstrip('www.')
        return any(domain == s or domain.endswith('.' + s) for s in SKIP_DOMAINS)
    except Exception:
        return False


def fetch_article_text(url: str, timeout: int = 15) -> Optional[str]:
    """Download a URL and extract clean article text with trafilatura."""
    if _should_skip(url):
        return None
    try:
        response = _SESSION.get(url, timeout=timeout)
        response.raise_for_status()
        text = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        if text and len(text.strip()) > 100:
            return text.strip()
    except Exception as e:
        logger.debug(f"Scrape failed for {url}: {e}")
    return None


def enrich_articles(articles: list[dict], delay: float = 0.5) -> list[dict]:
    """Fetch full text for each article; fall back to RSS description."""
    total = len(articles)
    for i, article in enumerate(articles):
        logger.info(f"Scraping [{i+1}/{total}]: {article['title'][:60]}")
        text = fetch_article_text(article['url'])
        if text:
            article['content'] = text
        else:
            # Fall back to the RSS description
            article['content'] = article.get('description', '')
        time.sleep(delay)
    return articles
