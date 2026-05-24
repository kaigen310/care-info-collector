"""RSS feed collector for care information aggregation."""

import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests
import yaml

_FEED_SESSION = requests.Session()
_FEED_SESSION.headers.update({'User-Agent': 'CareInfoBot/1.0'})

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def _parse_date(entry) -> str:
    """Extract and normalize publication date from a feed entry."""
    for field in ('published_parsed', 'updated_parsed', 'created_parsed'):
        t = getattr(entry, field, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc).astimezone(JST)
                return dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                pass
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M')


def collect_feeds(config_path: str = 'config/sources.yaml') -> list[dict]:
    """Read all RSS feeds defined in config and return a deduplicated article list."""
    config = yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))
    settings = config.get('settings', {})
    max_per_feed         = settings.get('max_articles_per_feed', 15)
    max_per_feed_en_care = settings.get('max_articles_per_feed_en_care', max_per_feed)
    delay = settings.get('request_delay', 1.0)

    seen_urls: set[str] = set()
    articles: list[dict] = []

    for feed_cfg in config.get('feeds', []):
        url = feed_cfg['url']
        name = feed_cfg['name']
        lang = feed_cfg.get('lang', 'ja')
        category_hint = feed_cfg.get('category', '未分類')

        content_type = feed_cfg.get('content_type', 'care')
        # 国内:海外 8:2 維持のため、海外careフィードは上限を絞る
        feed_max = max_per_feed
        if lang == 'en' and content_type == 'care':
            feed_max = max_per_feed_en_care

        try:
            logger.info(f"Fetching: {name} ({url})")
            # Use requests (which uses certifi for SSL) instead of feedparser's urllib
            resp = _FEED_SESSION.get(url, timeout=settings.get('request_timeout', 15))
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)

            if parsed.bozo and not parsed.entries:
                logger.warning(f"  Feed error for {name}: {parsed.bozo_exception}")
                continue

            count = 0
            for entry in parsed.entries[:feed_max]:
                link = getattr(entry, 'link', None)
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                title = getattr(entry, 'title', '').strip()
                description = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                description = _clean_html(description)[:500]

                articles.append({
                    'title': title,
                    'url': link,
                    'source': name,
                    'lang': lang,
                    'content_type': content_type,
                    'category_hint': category_hint,
                    'published': _parse_date(entry),
                    'description': description,
                    'content': '',
                    'summary': '',
                    'categories': [],
                })
                count += 1

            logger.info(f"  {count} new articles from {name}")
        except Exception as e:
            logger.error(f"  Failed to fetch {name}: {e}")

        time.sleep(delay)

    logger.info(f"Total collected: {len(articles)} articles from {len(config['feeds'])} feeds")
    return articles


def _clean_html(text: str) -> str:
    """Strip HTML tags and decode entities from text."""
    import re
    import html as _html
    text = re.sub(r'<[^>]+>', ' ', text)   # strip tags
    text = _html.unescape(text)             # &nbsp; → space, &amp; → & etc.
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
