"""Extractive text summarization — no API required, works offline.

Algorithm:
1. Split text into sentences.
2. Build a TF-IDF-like word-frequency vector for the whole document.
3. Score each sentence by the average frequency of its words.
4. Return the top-N sentences in their original order.
"""

import re
import math
from collections import Counter
from typing import Optional


_EN_STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'of', 'to', 'and',
    'or', 'for', 'with', 'that', 'this', 'it', 'be', 'have', 'has', 'had',
    'not', 'as', 'at', 'by', 'from', 'on', 'up', 'into', 'through', 'than',
    'its', 'we', 'our', 'they', 'their', 'he', 'she', 'his', 'her', 'who',
    'which', 'will', 'can', 'may', 'also', 'but', 'if', 'all', 'more', 'one',
}

_JA_STOPCHARS = set('。、！？「」『』【】（）・…　 \n\r\t')


def _split_sentences(text: str, lang: str) -> list[str]:
    if lang == 'ja':
        parts = re.split(r'(?<=[。！？])\s*', text)
    else:
        parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _tokenize(text: str, lang: str) -> list[str]:
    if lang == 'ja':
        # Character bigrams as approximate "words" for Japanese
        clean = re.sub(r'[^぀-鿿゠-ヿ＀-￯]', '', text)
        return [clean[i:i+2] for i in range(len(clean) - 1)]
    else:
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        return [w for w in words if w not in _EN_STOPWORDS]


def _score_sentence(sentence: str, freq: Counter, lang: str) -> float:
    tokens = _tokenize(sentence, lang)
    if not tokens:
        return 0.0
    return sum(freq.get(t, 0) for t in tokens) / len(tokens)


def summarize(text: str, lang: str = 'ja', num_sentences: int = 4) -> str:
    """Return a `num_sentences`-sentence extractive summary of `text`."""
    if not text or len(text) < 80:
        return text or ''

    sentences = _split_sentences(text, lang)
    if len(sentences) <= num_sentences:
        return text

    # Build corpus-level token frequency
    freq: Counter = Counter(_tokenize(text, lang))

    # Score and pick top sentences, preserving original order
    scored = [(_score_sentence(s, freq, lang), i, s) for i, s in enumerate(sentences)]
    top_indices = sorted(
        idx for _, idx, _ in sorted(scored, reverse=True)[:num_sentences]
    )

    if lang == 'ja':
        return '。'.join(sentences[i].rstrip('。') for i in top_indices) + '。'
    else:
        parts = [sentences[i].rstrip('.') for i in top_indices]
        return '. '.join(parts) + '.'


def _is_meaningful(summary: str, title: str) -> bool:
    """Return False if the summary is essentially just the title repeated."""
    import re
    import html as _html
    if not summary or len(summary.strip()) < 40:
        return False
    # Decode HTML entities before comparison so &nbsp; doesn't fool the check
    clean_s = re.sub(r'\s+', '', _html.unescape(summary).lower())
    clean_t = re.sub(r'\s+', '', _html.unescape(title).lower())
    if len(clean_t) > 0 and clean_s.startswith(clean_t[:min(len(clean_t), 30)]):
        return len(clean_s) > len(clean_t) * 1.5
    return True


def summarize_articles(articles: list[dict], num_sentences: int = 4) -> list[dict]:
    """Add a `summary` field to each article dict in-place."""
    for article in articles:
        content = article.get('content', '') or article.get('description', '')
        lang = article.get('lang', 'ja')
        title = article.get('title', '')
        raw = summarize(content, lang=lang, num_sentences=num_sentences)
        # Fall back to empty string if summary is just the title
        article['summary'] = raw if _is_meaningful(raw, title) else ''
    return articles
