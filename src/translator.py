"""Translate English article titles and summaries to Japanese.

Uses deep-translator + Google Translate free tier — no API key, no cost.
Rate-limited with delays to avoid throttling.
"""

import time
import logging

logger = logging.getLogger(__name__)

_MAX_CHARS = 4500   # Google Translate safe limit per request


def _translate_text(text: str, delay: float = 1.0) -> str:
    """Translate a single English text to Japanese. Falls back to original on error."""
    if not text or not text.strip():
        return text
    try:
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source='en', target='ja').translate(text[:_MAX_CHARS])
        time.sleep(delay)
        return result or text
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return text


def translate_articles(articles: list[dict], delay: float = 1.0) -> list[dict]:
    """Add `title_ja` and `summary_ja` fields to English articles."""
    en_articles = [a for a in articles if a.get('lang') == 'en']
    total = len(en_articles)
    if total == 0:
        return articles

    logger.info(f"Translating {total} English articles to Japanese…")
    for i, article in enumerate(en_articles):
        logger.info(f"  [{i+1}/{total}] {article.get('title','')[:55]}")
        article['title_ja']   = _translate_text(article.get('title', ''),   delay=delay)
        article['summary_ja'] = _translate_text(article.get('summary', ''), delay=delay)

    logger.info("Translation complete.")
    return articles
