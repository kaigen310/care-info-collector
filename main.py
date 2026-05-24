#!/usr/bin/env python3
"""
Care Info Collector — メインエントリポイント
毎日自動実行して介護・医療・福祉関連の情報を収集・要約・ダッシュボード化する。
"""

import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('collector.log', encoding='utf-8'),
    ],
)
logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def load_config(config_path: str = 'config/sources.yaml') -> dict:
    return yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))


def load_settings(config_path: str = 'config/sources.yaml') -> dict:
    return load_config(config_path).get('settings', {})


def _age_cutoff(settings: dict, content_type: str) -> 'datetime':
    """content_type ごとに異なる新鮮さの基準日を返す。"""
    days = {
        'care':      settings.get('max_article_age_days_care', 7),
        'tech':      settings.get('max_article_age_days_tech', 14),
        'lifestyle': settings.get('max_article_age_days_lifestyle', 60),
    }.get(content_type, settings.get('max_article_age_days_care', 7))
    return datetime.now(JST) - timedelta(days=days)


def apply_relevance_filter(articles: list[dict], config: dict) -> list[dict]:
    """ブロックリスト・古い記事・英語関連性チェックで無関係な記事を除外する。

    content_type ごとに異なるキーワードリストを使用:
      care      → 介護・高齢者ケア系キーワード
      tech      → AI・生産性系キーワード
      lifestyle → ストア哲学・メンタルケア系キーワード
    """
    settings = config.get('settings', {})
    blocklist       = [kw.lower() for kw in config.get('blocklist_keywords', [])]
    rel_care        = [kw.lower() for kw in config.get('relevance_keywords_en', [])]
    rel_tech        = [kw.lower() for kw in config.get('relevance_keywords_tech', [])]
    rel_lifestyle   = [kw.lower() for kw in config.get('relevance_keywords_lifestyle', [])]

    kept, removed = [], []
    for a in articles:
        text = ((a.get('title') or '') + ' ' + (a.get('summary') or '')).lower()

        # 1. ブロックリスト（感染症アウトブレイクなど明らかに無関係なトピック）
        if any(kw in text for kw in blocklist):
            removed.append(('blocklist', a['title'][:50]))
            continue

        # 2. 古い記事フィルタ（content_type ごとに異なる期限を適用）
        pub = a.get('published', '')
        if pub:
            try:
                ct = a.get('content_type', 'care')
                d  = datetime.fromisoformat(pub.replace(' ', 'T') + '+09:00')
                if d < _age_cutoff(settings, ct):
                    removed.append(('old', a['title'][:50]))
                    continue
            except ValueError:
                pass

        # 3. 英語記事の関連性チェック（content_type に応じたキーワードを使用）
        if a.get('lang') == 'en':
            ct = a.get('content_type', 'care')
            if ct == 'tech':
                keywords = rel_tech
            elif ct == 'lifestyle':
                keywords = rel_lifestyle
            else:
                keywords = rel_care

            if keywords and not any(kw in text for kw in keywords):
                removed.append((f'irrelevant_{ct}', a['title'][:50]))
                continue

        kept.append(a)

    for reason, title in removed:
        logger.info(f"  除外 [{reason}]: {title}")
    logger.info(f"関連性フィルタ: {len(removed)}件除外 → {len(kept)}件残存")
    return kept


def purge_old_data(data_dir: Path, days_to_keep: int) -> None:
    """Delete JSON data files older than `days_to_keep` days."""
    cutoff = datetime.now(JST).date() - timedelta(days=days_to_keep)
    for f in data_dir.glob('articles_*.json'):
        try:
            file_date_str = f.stem.replace('articles_', '')
            file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
            if file_date < cutoff:
                f.unlink()
                logger.info(f"Purged old data file: {f.name}")
        except ValueError:
            pass


def main() -> int:
    from src.collector import collect_feeds
    from src.scraper import enrich_articles
    from src.summarizer import summarize_articles
    from src.classifier import classify_articles
    from src.translator import translate_articles
    from src.generator import generate_dashboard

    config   = load_config()
    settings = config.get('settings', {})
    data_dir = Path(settings.get('data_dir', 'data'))
    output_dir = settings.get('output_dir', 'docs')
    days_to_keep = settings.get('days_to_keep', 30)
    num_sentences = settings.get('summary_sentences', 4)

    data_dir.mkdir(exist_ok=True)

    today = datetime.now(JST).strftime('%Y-%m-%d')
    logger.info(f"=== Care Info Collector started: {today} ===")

    # 1. Collect RSS feeds
    logger.info("Step 1: Collecting RSS feeds…")
    articles = collect_feeds()
    if not articles:
        logger.warning("No articles collected. Check feed URLs in config/sources.yaml")
        return 1

    # 2. Scrape full article content
    logger.info("Step 2: Scraping article content…")
    articles = enrich_articles(articles)

    # 3. Extractive summarization (no API cost)
    logger.info("Step 3: Generating summaries…")
    articles = summarize_articles(articles, num_sentences=num_sentences)

    # 4. 要約が取得できなかった記事（有料・取得不可）を除外
    before = len(articles)
    articles = [a for a in articles if a.get('summary') and len(a['summary'].strip()) > 50]
    logger.info(f"要約なし除外: {before - len(articles)}件 → {len(articles)}件残存")

    if not articles:
        logger.warning("No articles with summaries. All may be paywalled.")
        return 1

    # 4b. 関連性フィルタ（ブロックリスト・古い記事・英語関連性）
    logger.info("Step 4b: 関連性フィルタを適用…")
    articles = apply_relevance_filter(articles, config)

    if not articles:
        logger.warning("No articles passed relevance filter.")
        return 1

    # 4c. 英語記事の総数キャップ（8:2 比率の最終調整）
    max_en_total = settings.get('max_articles_en_total', 10)
    en_articles = [a for a in articles if a.get('lang') == 'en']
    ja_articles = [a for a in articles if a.get('lang') != 'en']
    if len(en_articles) > max_en_total:
        # content_type 別に均等割り当て（care/tech/lifestyle からまんべんなく）
        from collections import defaultdict
        ct_buckets: dict = defaultdict(list)
        for a in sorted(en_articles, key=lambda x: x.get('published', ''), reverse=True):
            ct_buckets[a.get('content_type', 'care')].append(a)

        selected: list = []
        # care → tech → lifestyle の優先順で交互に取る
        order = ['care', 'tech', 'lifestyle']
        while len(selected) < max_en_total:
            added = False
            for ct in order:
                if len(selected) >= max_en_total:
                    break
                if ct_buckets[ct]:
                    selected.append(ct_buckets[ct].pop(0))
                    added = True
            if not added:
                break

        logger.info(f"英語記事キャップ: {len(en_articles)}件 → {len(selected)}件 (上限 {max_en_total})")
        en_articles = selected

    articles = ja_articles + en_articles
    logger.info(f"言語比率: 日本語 {len(ja_articles)}件 / 英語 {len(en_articles)}件")

    # 5. 英語記事のタイトル・要約を日本語に翻訳
    logger.info("Step 5: Translating English articles…")
    articles = translate_articles(articles)

    # 6. Classify into categories
    logger.info("Step 6: Classifying articles…")
    articles = classify_articles(articles)

    # 7. Sort by date (newest first)
    articles.sort(key=lambda a: a.get('published', ''), reverse=True)

    # 8. Save JSON data
    data_file = data_dir / f'articles_{today}.json'
    data_file.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info(f"Saved {len(articles)} articles → {data_file}")

    # 9. Generate HTML dashboard
    logger.info("Step 9: Generating HTML dashboard…")
    generate_dashboard(articles, date_str=today, output_dir=output_dir)

    # 10. Purge old data files
    purge_old_data(data_dir, days_to_keep)

    logger.info(f"=== Done: {len(articles)} articles processed ===")
    return 0


if __name__ == '__main__':
    sys.exit(main())
