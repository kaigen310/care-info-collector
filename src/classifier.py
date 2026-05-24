"""Keyword-based article category classifier."""

from __future__ import annotations

CATEGORIES: dict[str, dict] = {
    # ── 国内コア ────────────────────────────────────────────────────
    '介護保険・制度': {
        'ja': ['介護保険', '要介護', '要支援', '認定', '給付', '保険料', '介護報酬',
               '地域包括', '制度改正', '介護給付費', '居宅', '施設給付', '地域密着',
               '総合事業', '社会保障審議会', '厚生労働省', '報酬改定'],
        'en': ['long-term care insurance', 'care insurance', 'insurance reform',
               'care policy', 'care allowance', 'care benefit', 'ltci'],
        'color': '#2563EB',
        'icon': '📋',
    },
    '医療・健康': {
        'ja': ['医療', '病院', '診療', '医師', '看護', '薬', '治療', '疾患', '健康',
               '予防', 'リハビリ', '認知症', '糖尿病', '高血圧', '在宅医療', '訪問看護'],
        'en': ['medical', 'health', 'hospital', 'nursing', 'treatment', 'disease',
               'clinical', 'healthcare', 'rehabilitation', 'dementia', 'geriatric'],
        'color': '#DC2626',
        'icon': '🏥',
    },
    '福祉・社会保障': {
        'ja': ['福祉', '社会保障', '生活保護', '障害', '高齢者', '子育て', '支援',
               '包括ケア', 'ケアマネ', '地域福祉', 'セーフティネット', '権利擁護'],
        'en': ['welfare', 'social security', 'disability', 'elderly care',
               'social care', 'support', 'social work', 'social worker', 'community care'],
        'color': '#059669',
        'icon': '🤝',
    },
    '施設運営・経営': {
        'ja': ['施設', '運営', '経営', '特養', 'デイサービス', 'グループホーム',
               '老健', '有料老人ホーム', '管理', 'サービス付き', '入所', '利用者', '収支',
               '赤字', '黒字', '加算', '減算'],
        'en': ['facility', 'nursing home', 'assisted living', 'senior care',
               'management', 'operations', 'care facility', 'elder care', 'skilled nursing',
               'occupancy', 'staffing ratio', 'resident'],
        'color': '#D97706',
        'icon': '🏢',
    },
    '人材育成・HR': {
        'ja': ['人材', '採用', '育成', '研修', '職員', 'スタッフ', '介護士',
               '介護福祉士', '離職', '定着', 'キャリア', '資格', '処遇改善',
               '賃上げ', '外国人', '特定技能'],
        'en': ['workforce', 'recruitment', 'training', 'staff', 'caregiver',
               'human resources', 'retention', 'career', 'qualification', 'diversity'],
        'color': '#7C3AED',
        'icon': '👥',
    },
    '業務改善・介護テック': {
        'ja': ['DX', 'AI', 'ICT', '業務改善', '効率化', 'ロボット', 'テクノロジー',
               'デジタル', 'システム', 'IoT', 'センサー', '介護ロボ', 'アプリ',
               '自動化', 'IT', 'ケアテック', '見守り', 'センシング'],
        'en': ['technology', 'digital', 'AI', 'robot', 'automation', 'innovation',
               'digital transformation', 'IoT', 'software', 'app', 'system', 'tool',
               'caretech', 'agetech', 'age tech', 'wearable', 'monitoring'],
        'color': '#0891B2',
        'icon': '💡',
    },
    '組織・心理': {
        'ja': ['組織', '心理', 'モチベーション', 'チームワーク', 'リーダーシップ',
               'バーンアウト', 'ストレス', 'コミュニケーション', '燃え尽き',
               '職場環境', '働き方', 'メンタル'],
        'en': ['organizational', 'psychology', 'motivation', 'burnout', 'leadership',
               'communication', 'team', 'workplace', 'wellbeing', 'mental health',
               'compassion fatigue'],
        'color': '#EA580C',
        'icon': '🧠',
    },
    # ── 海外スパイス ────────────────────────────────────────────────
    '海外エイジテック': {
        'ja': ['エイジテック', '高齢者テック', 'シニアテック'],
        'en': ['agetech', 'age tech', 'senior tech', 'aging technology', 'gerontechnology',
               'assistive technology', 'aging innovation', 'silver economy', 'senior living tech',
               'remote patient monitoring', 'fall detection', 'smart home aging'],
        'color': '#0D9488',
        'icon': '🔬',
    },
    'AIツール・生産性': {
        'ja': ['生産性', 'ワークフロー', 'ノーション', 'Notion', 'オブシディアン'],
        'en': ['AI agent', 'AI tool', 'automation workflow', 'productivity', 'notion',
               'obsidian', 'large language model', 'llm', 'chatgpt', 'claude', 'copilot',
               'no-code', 'zapier', 'n8n', 'make.com', 'generative AI', 'prompt'],
        'color': '#6D28D9',
        'icon': '⚡',
    },
    'メンタル・哲学': {
        'ja': ['ストア哲学', 'ストイック', 'マインドフルネス', '瞑想', '哲学', '内省'],
        'en': ['stoic', 'stoicism', 'marcus aurelius', 'seneca', 'epictetus',
               'mindfulness', 'meditation', 'resilience', 'self-improvement',
               'mental fortitude', 'philosophy', 'inner peace', 'journaling'],
        'color': '#BE185D',
        'icon': '🌿',
    },
}

DEFAULT_CATEGORY = '福祉・社会保障'


def classify(title: str, content: str, lang: str, category_hint: str = '') -> list[str]:
    text = (title + ' ' + content[:1000]).lower()
    scores: dict[str, int] = {}

    for cat_name, cfg in CATEGORIES.items():
        keywords = cfg.get(lang, cfg.get('ja', []))
        count = sum(text.count(kw.lower()) for kw in keywords)
        if count > 0:
            scores[cat_name] = count

    if not scores:
        for cat_name in CATEGORIES:
            if category_hint and cat_name == category_hint:
                return [cat_name]
        return [DEFAULT_CATEGORY]

    top = sorted(scores, key=lambda k: scores[k], reverse=True)[:2]
    return top


def classify_articles(articles: list[dict]) -> list[dict]:
    for article in articles:
        article['categories'] = classify(
            article.get('title', ''),
            article.get('content', '') or article.get('description', ''),
            article.get('lang', 'ja'),
            article.get('category_hint', ''),
        )
    return articles


def category_meta(name: str) -> dict:
    return CATEGORIES.get(name, {'color': '#6B7280', 'icon': '📰'})
