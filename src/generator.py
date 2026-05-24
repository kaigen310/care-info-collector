"""Static HTML dashboard generator — modern Shadcn/ui-inspired design."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.classifier import CATEGORIES

JST = timezone(timedelta(hours=9))


def _escape(text: str) -> str:
    return (text
            .replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def generate_dashboard(articles: list[dict], date_str: str, output_dir: str = 'docs') -> None:
    """Generate a self-contained HTML dashboard and write it to docs/index.html."""
    updated_at = datetime.now(JST).strftime('%Y年%m月%d日 %H:%M JST')
    articles_json = json.dumps(articles, ensure_ascii=False)

    cat_meta_json = json.dumps({
        name: {'color': cfg['color'], 'icon': cfg['icon']}
        for name, cfg in CATEGORIES.items()
    }, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>介護情報ダッシュボード — {date_str}</title>
<style>
/* ── Design Tokens ─────────────────────────────────────────── */
:root {{
  --bg:            #f9fafb;
  --surface:       #ffffff;
  --surface-2:     #f3f4f6;
  --border:        #e5e7eb;
  --border-light:  #f0f0f0;
  --text:          #1f2937;
  --text-sub:      #374151;
  --muted:         #9ca3af;
  --muted-dark:    #6b7280;

  /* アクセント: セージ寄りのティール */
  --accent:        #0d9488;
  --accent-hover:  #0f766e;
  --accent-light:  #f0fdfa;
  --accent-mid:    #ccfbf1;

  /* 新しさバッジ */
  --badge-new-bg:  #d1fae5;
  --badge-new-fg:  #065f46;
  --badge-week-bg: #fef3c7;
  --badge-week-fg: #92400e;
  --badge-old-bg:  #f3f4f6;
  --badge-old-fg:  #6b7280;

  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius:    12px;
  --radius-lg: 16px;

  --shadow-xs: 0 1px 2px rgba(0,0,0,.05);
  --shadow-sm: 0 1px 3px rgba(0,0,0,.08), 0 1px 6px rgba(0,0,0,.04);
  --shadow-md: 0 4px 16px rgba(0,0,0,.10), 0 2px 6px rgba(0,0,0,.06);

  --transition: 0.18s ease;

  --font: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN",
          "Hiragino Sans", "Yu Gothic UI", "Noto Sans JP", sans-serif;
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:           #0f172a;
    --surface:      #1e293b;
    --surface-2:    #293548;
    --border:       #334155;
    --border-light: #1e293b;
    --text:         #f1f5f9;
    --text-sub:     #cbd5e1;
    --muted:        #64748b;
    --muted-dark:   #94a3b8;
    --accent:       #2dd4bf;
    --accent-hover: #5eead4;
    --accent-light: #0f2d2a;
    --accent-mid:   #134e4a;
    --badge-old-bg: #1e293b;
    --badge-old-fg: #94a3b8;
  }}
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.65;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
button {{ font-family: var(--font); cursor: pointer; }}
:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--radius-sm); }}


/* ── Topbar ─────────────────────────────────────────────────── */
.topbar {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 1.75rem;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  position: sticky;
  top: 0;
  z-index: 300;
  box-shadow: var(--shadow-xs);
}}

.topbar-logo {{
  display: flex;
  align-items: center;
  gap: .5rem;
  font-size: 1.05rem;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: -.01em;
}}
.topbar-logo-icon {{
  width: 30px; height: 30px;
  background: var(--accent);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: .9rem;
}}
.topbar-logo-text {{ color: var(--text); }}
.topbar-logo-text em {{
  font-style: normal;
  color: var(--accent);
}}

.search-wrap {{
  flex: 1;
  max-width: 360px;
  position: relative;
}}
.search-icon {{
  position: absolute;
  left: .85rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  pointer-events: none;
}}
.search-input {{
  width: 100%;
  padding: .55rem 1rem .55rem 2.4rem;
  background: var(--surface-2);
  border: 1.5px solid var(--border);
  border-radius: 9999px;
  color: var(--text);
  font-size: .88rem;
  font-family: var(--font);
  outline: none;
  transition: border-color var(--transition), background var(--transition);
}}
.search-input:focus {{
  border-color: var(--accent);
  background: var(--surface);
}}
.search-input::placeholder {{ color: var(--muted); }}

.topbar-updated {{
  font-size: .78rem;
  color: var(--muted-dark);
  margin-left: auto;
  white-space: nowrap;
}}


/* ── Stats bar ──────────────────────────────────────────────── */
.statsbar {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 1.75rem;
  height: 44px;
  display: flex;
  align-items: center;
  gap: .5rem;
  font-size: .82rem;
  color: var(--muted-dark);
  overflow-x: auto;
}}
.statsbar::-webkit-scrollbar {{ display: none; }}

.stat-chip {{
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  padding: .2rem .7rem;
  border-radius: 9999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  white-space: nowrap;
  font-size: .8rem;
}}
.stat-chip strong {{
  color: var(--text);
  font-size: .92rem;
  font-weight: 600;
}}
.stats-spacer {{ flex: 1; }}
#resultCount {{
  font-size: .8rem;
  color: var(--muted-dark);
  white-space: nowrap;
}}
#resultCount strong {{ color: var(--text); font-weight: 600; }}


/* ── Filter Bar ─────────────────────────────────────────────── */
.filterbar {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 1.75rem;
  display: flex;
  align-items: center;
  gap: 0;
  position: sticky;
  top: 60px;
  z-index: 200;
}}

/* Time period tabs — underline style */
.period-tabs {{
  display: flex;
  align-items: stretch;
  flex-shrink: 0;
  height: 48px;
}}
.period-tab {{
  padding: 0 1.05rem;
  border: none;
  border-bottom: 2.5px solid transparent;
  background: transparent;
  color: var(--muted-dark);
  font-size: .875rem;
  font-weight: 500;
  white-space: nowrap;
  transition: color var(--transition), border-color var(--transition);
}}
.period-tab:hover {{ color: var(--text); }}
.period-tab.active {{
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}}

.filterbar-sep {{
  width: 1px;
  background: var(--border);
  margin: 10px 0;
  flex-shrink: 0;
}}

/* Category chips — pill style */
.cat-chips-wrap {{
  flex: 1;
  overflow-x: auto;
  display: flex;
  align-items: center;
  gap: .45rem;
  padding: 0 1rem;
  scrollbar-width: none;
  height: 48px;
}}
.cat-chips-wrap::-webkit-scrollbar {{ display: none; }}

.cat-chip {{
  flex-shrink: 0;
  padding: .28rem .85rem;
  border-radius: 9999px;
  border: 1.5px solid var(--border);
  background: transparent;
  color: var(--muted-dark);
  font-size: .8rem;
  font-weight: 500;
  white-space: nowrap;
  transition: all var(--transition);
  line-height: 1.4;
}}
.cat-chip:hover {{
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-light);
}}
.cat-chip.active {{
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 600;
}}

/* Right controls */
.right-controls {{
  display: flex;
  align-items: center;
  gap: .5rem;
  flex-shrink: 0;
  padding-left: .75rem;
  height: 48px;
}}

.ctrl-select {{
  appearance: none;
  -webkit-appearance: none;
  padding: .35rem 2rem .35rem .75rem;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border);
  background: var(--surface-2) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 20 20' fill='%239ca3af'%3E%3Cpath fill-rule='evenodd' d='M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z'/%3E%3C/svg%3E") no-repeat right .6rem center;
  color: var(--text);
  font-size: .82rem;
  font-family: var(--font);
  outline: none;
  cursor: pointer;
  transition: border-color var(--transition);
}}
.ctrl-select:focus {{ border-color: var(--accent); }}


/* ── Main Layout ────────────────────────────────────────────── */
.main-wrap {{
  max-width: 1280px;
  margin: 0 auto;
  padding: 1.75rem 1.75rem 3rem;
  display: flex;
  gap: 1.75rem;
  align-items: flex-start;
}}


/* ── Sidebar ─────────────────────────────────────────────────── */
.sidebar {{
  width: 230px;
  flex-shrink: 0;
  position: sticky;
  top: 112px;
}}
.sidebar-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow-xs);
}}
.sidebar-title {{
  font-size: .72rem;
  font-weight: 700;
  color: var(--muted-dark);
  letter-spacing: .07em;
  text-transform: uppercase;
  margin-bottom: .65rem;
  padding-bottom: .5rem;
  border-bottom: 1px solid var(--border-light);
}}
.sidebar-item {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: .42rem .5rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-sub);
  font-size: .83rem;
  text-align: left;
  cursor: pointer;
  transition: background var(--transition), color var(--transition);
  gap: .4rem;
}}
.sidebar-item:hover {{ background: var(--surface-2); }}
.sidebar-item.active {{
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 600;
}}
.sidebar-item-label {{ flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.sidebar-count {{
  flex-shrink: 0;
  font-size: .72rem;
  padding: 1px 7px;
  border-radius: 9999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--muted-dark);
  font-weight: 500;
  min-width: 28px;
  text-align: center;
}}
.sidebar-item.active .sidebar-count {{
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}}


/* ── Articles column ─────────────────────────────────────────── */
.articles-col {{ flex: 1; min-width: 0; }}


/* ── Section header (category-sort mode) ───────────────────── */
.section-header {{
  display: flex;
  align-items: center;
  gap: .65rem;
  margin: 1.75rem 0 .9rem;
  padding-bottom: .6rem;
  border-bottom: 2px solid var(--border);
}}
.section-header:first-child {{ margin-top: 0; }}
.section-icon {{ font-size: 1.15rem; }}
.section-name {{
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
}}
.section-count {{
  font-size: .76rem;
  padding: 2px 9px;
  border-radius: 9999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--muted-dark);
  font-weight: 500;
}}


/* ── Article Card ────────────────────────────────────────────── */
.article-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 1rem;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow var(--transition), transform var(--transition), border-color var(--transition);
  will-change: transform;
}}
.article-card:hover {{
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: #d1d5db;
}}

/* Card top band */
.card-band {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: .5rem;
  padding: .75rem 1.25rem .65rem;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border-light);
}}
.card-cats {{ display: flex; flex-wrap: wrap; gap: .35rem; flex: 1; min-width: 0; }}
.cat-badge {{
  font-size: .71rem;
  padding: 2px 10px;
  border-radius: 9999px;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: .01em;
}}
.card-meta {{
  display: flex;
  align-items: center;
  gap: .45rem;
  flex-shrink: 0;
}}

/* Age badge */
.age-badge {{
  font-size: .72rem;
  padding: 2px 9px;
  border-radius: 9999px;
  font-weight: 600;
  white-space: nowrap;
}}
.age-new  {{ background: var(--badge-new-bg);  color: var(--badge-new-fg);  }}
.age-week {{ background: var(--badge-week-bg); color: var(--badge-week-fg); }}
.age-old  {{ background: var(--badge-old-bg);  color: var(--badge-old-fg);  }}

/* Language badge */
.lang-badge {{
  font-size: .68rem;
  padding: 1px 7px;
  border-radius: var(--radius-xs);
  font-weight: 700;
  white-space: nowrap;
}}
.lang-ja {{ background: #fef3c7; color: #92400e; }}
.lang-en {{ background: #dbeafe; color: #1e40af; }}

/* Translation badge */
.trans-badge {{
  font-size: .68rem;
  padding: 1px 7px;
  border-radius: var(--radius-xs);
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
  font-weight: 600;
  white-space: nowrap;
}}

/* Card body — summary is the hero */
.card-body {{
  padding: 1.1rem 1.25rem .85rem;
}}
.card-summary {{
  font-size: .95rem;
  line-height: 1.8;
  color: var(--text);
  margin-bottom: 0;
}}
.card-summary-empty {{
  font-size: .875rem;
  color: var(--muted-dark);
  font-style: italic;
  padding: .2rem 0;
}}

/* Card footer */
.card-footer {{
  padding: .7rem 1.25rem .85rem;
  border-top: 1px solid var(--border-light);
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: .75rem;
}}
.card-footer-left {{ flex: 1; min-width: 0; }}
.card-source {{
  font-size: .75rem;
  color: var(--muted-dark);
  margin-bottom: .25rem;
  display: flex;
  align-items: center;
  gap: .4rem;
}}
.card-source-dot {{ color: var(--border); }}
.card-title {{
  font-size: .88rem;
  font-weight: 600;
  color: var(--text-sub);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.55;
  transition: color var(--transition);
}}
.card-title:hover {{ color: var(--accent); text-decoration: none; }}

/* Read button */
.read-btn {{
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: .3rem;
  padding: .45rem 1rem;
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  border: 1.5px solid var(--border);
  color: var(--muted-dark);
  font-size: .8rem;
  font-weight: 600;
  white-space: nowrap;
  transition: all var(--transition);
}}
.read-btn:hover {{
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  text-decoration: none;
}}
.read-btn svg {{ transition: transform var(--transition); }}
.read-btn:hover svg {{ transform: translateX(2px); }}


/* ── Empty state ─────────────────────────────────────────────── */
.empty-state {{
  display: none;
  text-align: center;
  padding: 4rem 1.5rem;
  color: var(--muted-dark);
}}
.empty-state-icon {{
  font-size: 2.5rem;
  margin-bottom: .75rem;
  opacity: .5;
}}
.empty-state p {{ font-size: .95rem; line-height: 1.7; }}


/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 900px) {{
  .sidebar {{ display: none; }}
}}
@media (max-width: 640px) {{
  .main-wrap {{ padding: 1rem .75rem 3rem; gap: 1rem; }}
  .topbar {{ padding: 0 1rem; }}
  .statsbar, .filterbar {{ padding: 0 1rem; }}
  .topbar-updated {{ display: none; }}
}}
</style>
</head>
<body>

<!-- ─── Topbar ─────────────────────────────────────────────── -->
<header class="topbar">
  <div class="topbar-logo">
    <div class="topbar-logo-icon">🏥</div>
    <span class="topbar-logo-text">介護情報<em>DB</em></span>
  </div>
  <div class="search-wrap">
    <svg class="search-icon" width="15" height="15" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
    </svg>
    <input class="search-input" type="search" id="searchInput" placeholder="タイトル・要約・情報源を検索…" autocomplete="off" />
  </div>
  <div class="topbar-updated">最終更新: {updated_at}</div>
</header>

<!-- ─── Stats bar ──────────────────────────────────────────── -->
<div class="statsbar" role="status" aria-live="polite">
  <div class="stat-chip">📰 合計 <strong id="statTotal">—</strong></div>
  <div class="stat-chip">🇯🇵 国内 <strong id="statJa">—</strong></div>
  <div class="stat-chip">🌐 海外 <strong id="statEn">—</strong></div>
  <div class="stat-chip">🆕 今日 <strong id="statToday">—</strong></div>
  <div class="stats-spacer"></div>
  <div id="resultCount">表示中: <strong id="visibleCount">—</strong> 件</div>
</div>

<!-- ─── Filter bar ─────────────────────────────────────────── -->
<nav class="filterbar" aria-label="フィルター">
  <div class="period-tabs" role="tablist" aria-label="期間">
    <button class="period-tab" role="tab" data-period="today">🆕 今日</button>
    <button class="period-tab" role="tab" data-period="week">今週</button>
    <button class="period-tab" role="tab" data-period="month">今月</button>
    <button class="period-tab active" role="tab" data-period="all" aria-selected="true">すべて</button>
  </div>
  <div class="filterbar-sep" aria-hidden="true"></div>
  <div class="cat-chips-wrap" id="catChips" role="group" aria-label="カテゴリ">
    <button class="cat-chip active" data-cat="all">すべて</button>
  </div>
  <div class="filterbar-sep" aria-hidden="true"></div>
  <div class="right-controls">
    <label class="sr-only" for="langFilter">言語フィルター</label>
    <select class="ctrl-select" id="langFilter" aria-label="言語フィルター">
      <option value="all">🌐 全言語</option>
      <option value="ja">🇯🇵 日本語</option>
      <option value="en">🇺🇸 English</option>
    </select>
    <label class="sr-only" for="sortBy">並び順</label>
    <select class="ctrl-select" id="sortBy" aria-label="並び順">
      <option value="date">新着順</option>
      <option value="cat">カテゴリ順</option>
    </select>
  </div>
</nav>

<!-- ─── Main ───────────────────────────────────────────────── -->
<div class="main-wrap">

  <!-- Sidebar -->
  <aside class="sidebar" aria-label="フィルターサイドバー">
    <div class="sidebar-card">
      <div class="sidebar-title">カテゴリ</div>
      <div id="sidebarCats"></div>
    </div>
    <div class="sidebar-card">
      <div class="sidebar-title">情報源</div>
      <div id="sidebarSources"></div>
    </div>
  </aside>

  <!-- Article list -->
  <main class="articles-col" id="articlesMain">
    <div id="articlesContainer" aria-label="記事一覧"></div>
    <div class="empty-state" id="emptyState" role="alert">
      <div class="empty-state-icon">🔍</div>
      <p>条件に一致する記事がありませんでした。<br>検索語・カテゴリ・期間を変えてみてください。</p>
    </div>
  </main>

</div>

<script>
// ── Data ─────────────────────────────────────────────────────────
const ARTICLES = {articles_json};
const CAT_META  = {cat_meta_json};
const DEFAULT_CLR = '#6b7280';

// ── State ────────────────────────────────────────────────────────
let state = {{ period:'all', cat:'all', lang:'all', sort:'date', search:'' }};

// ── Utils ────────────────────────────────────────────────────────
const esc = s => String(s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function parseDate(s) {{
  if (!s) return new Date(0);
  return new Date(s.replace(' ','T') + (s.length===10?'T00:00:00+09:00':'+09:00'));
}}

function ageBucket(d) {{
  const h = (Date.now() - parseDate(d)) / 3.6e6;
  if (h < 48) return 'new';
  if (h < 168) return 'week';
  return 'old';
}}

function ageBadgeHtml(dateStr) {{
  const d = parseDate(dateStr);
  const h = (Date.now() - d) / 3.6e6;
  let label, cls;
  if (h < 24)       {{ label='今日';            cls='age-new';  }}
  else if (h < 48)  {{ label='昨日';            cls='age-new';  }}
  else if (h < 168) {{ label=Math.floor(h/24)+'日前'; cls='age-week'; }}
  else              {{ label=d.toLocaleDateString('ja-JP',{{month:'short',day:'numeric'}}); cls='age-old'; }}
  return `<span class="age-badge ${{cls}}">${{label}}</span>`;
}}

function catBadgesHtml(cats) {{
  return (cats||[]).map(c => {{
    const m = CAT_META[c] || {{color:DEFAULT_CLR,icon:'📰'}};
    const clr = m.color;
    return `<span class="cat-badge" style="background:${{clr}}18;color:${{clr}};border:1px solid ${{clr}}35">` +
           `${{m.icon}} ${{esc(c)}}</span>`;
  }}).join('');
}}

// ── Card builder ─────────────────────────────────────────────────
function buildCard(a) {{
  const displaySummary = (a.lang==='en' && a.summary_ja) ? a.summary_ja : (a.summary||'');
  const displayTitle   = (a.lang==='en' && a.title_ja)   ? a.title_ja   : (a.title||'');
  const isEn = a.lang === 'en';

  const langBadge  = isEn
    ? '<span class="lang-badge lang-en">EN</span>'
    : '<span class="lang-badge lang-ja">JP</span>';
  const transBadge = isEn ? '<span class="trans-badge">🌐 翻訳</span>' : '';

  const summaryBlock = displaySummary.trim().length > 30
    ? `<p class="card-summary">${{esc(displaySummary)}}</p>`
    : `<p class="card-summary-empty">要約を取得できませんでした</p>`;

  const publishedDate = (a.published||'').slice(0,10);

  return `<article class="article-card"
  data-cats="${{esc(JSON.stringify(a.categories||[]))}}"
  data-lang="${{a.lang||'ja'}}"
  data-date="${{a.published||''}}"
  data-source="${{esc(a.source||'')}}"
  data-search="${{esc(((a.title_ja||a.title)+' '+(a.summary_ja||a.summary||'')+' '+a.source).toLowerCase())}}">

  <div class="card-band">
    <div class="card-cats">${{catBadgesHtml(a.categories)}}</div>
    <div class="card-meta">
      ${{ageBadgeHtml(a.published)}}
      ${{transBadge}}
      ${{langBadge}}
    </div>
  </div>

  <div class="card-body">
    ${{summaryBlock}}
  </div>

  <div class="card-footer">
    <div class="card-footer-left">
      <div class="card-source">
        <span>${{esc(a.source)}}</span>
        <span class="card-source-dot">·</span>
        <span>${{publishedDate}}</span>
      </div>
      <a class="card-title" href="${{esc(a.url)}}" target="_blank" rel="noopener noreferrer">
        ${{esc(displayTitle)}}
      </a>
    </div>
    <a class="read-btn" href="${{esc(a.url)}}" target="_blank" rel="noopener noreferrer" aria-label="記事を読む">
      記事を読む
      <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd"/>
      </svg>
    </a>
  </div>
</article>`;
}}

// ── Filter ───────────────────────────────────────────────────────
function filterArticles() {{
  const now = Date.now();
  return ARTICLES.filter(a => {{
    if (state.period !== 'all') {{
      const h = (now - parseDate(a.published)) / 3.6e6;
      if (state.period==='today' && h>48)  return false;
      if (state.period==='week'  && h>168) return false;
      if (state.period==='month' && h>720) return false;
    }}
    if (state.cat  !== 'all' && !(a.categories||[]).includes(state.cat)) return false;
    if (state.lang !== 'all' && a.lang !== state.lang) return false;
    if (state.search) {{
      const q = state.search.toLowerCase();
      const hay = ((a.title_ja||a.title)+' '+(a.summary_ja||a.summary||'')+' '+a.source).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }}).sort((a,b) => {{
    if (state.sort==='date') return parseDate(b.published)-parseDate(a.published);
    const ca=(a.categories||[''])[0]||'', cb=(b.categories||[''])[0]||'';
    return ca!==cb ? ca.localeCompare(cb,'ja') : parseDate(b.published)-parseDate(a.published);
  }});
}}

// ── Section header ───────────────────────────────────────────────
function sectionHeader(catName, count) {{
  const m = CAT_META[catName] || {{color:DEFAULT_CLR, icon:'📰'}};
  return `<div class="section-header">
    <span class="section-icon">${{m.icon}}</span>
    <span class="section-name" style="color:${{m.color}}">${{esc(catName)}}</span>
    <span class="section-count">${{count}}件</span>
  </div>`;
}}

// ── Render ───────────────────────────────────────────────────────
function render() {{
  const filtered = filterArticles();
  const container = document.getElementById('articlesContainer');
  const empty = document.getElementById('emptyState');
  document.getElementById('visibleCount').textContent = filtered.length;

  if (!filtered.length) {{
    container.innerHTML = '';
    empty.style.display = 'block';
    renderSidebar(filtered);
    return;
  }}
  empty.style.display = 'none';

  if (state.sort==='cat' && state.cat==='all') {{
    const groups = {{}};
    const ORDER = Object.keys(CAT_META);
    filtered.forEach(a => {{
      const c = (a.categories||[])[0] || '未分類';
      (groups[c]=groups[c]||[]).push(a);
    }});
    let html='';
    ORDER.forEach(c => {{
      if (groups[c]?.length) html += sectionHeader(c,groups[c].length)+groups[c].map(buildCard).join('');
    }});
    if (groups['未分類']?.length) html += sectionHeader('未分類',groups['未分類'].length)+groups['未分類'].map(buildCard).join('');
    container.innerHTML = html;
  }} else {{
    container.innerHTML = filtered.map(buildCard).join('');
  }}

  renderSidebar(filtered);
}}

// ── Sidebar render ───────────────────────────────────────────────
function renderSidebar(filtered) {{
  const catCounts={{}}, srcCounts={{}};
  filtered.forEach(a => {{
    (a.categories||[]).forEach(c=>{{ catCounts[c]=(catCounts[c]||0)+1; }});
    srcCounts[a.source]=(srcCounts[a.source]||0)+1;
  }});

  // Categories
  const sidebarCats = document.getElementById('sidebarCats');
  let html = `<button class="sidebar-item ${{state.cat==='all'?'active':''}}" data-scat="all">
    <span class="sidebar-item-label">すべて</span>
    <span class="sidebar-count">${{filtered.length}}</span>
  </button>`;
  Object.entries(catCounts).sort((a,b)=>b[1]-a[1]).forEach(([cat,cnt]) => {{
    const m = CAT_META[cat]||{{icon:'📰'}};
    html += `<button class="sidebar-item ${{state.cat===cat?'active':''}}" data-scat="${{esc(cat)}}">
      <span class="sidebar-item-label">${{m.icon}} ${{esc(cat)}}</span>
      <span class="sidebar-count">${{cnt}}</span>
    </button>`;
  }});
  sidebarCats.innerHTML = html;

  // Sources
  const sidebarSrc = document.getElementById('sidebarSources');
  let srcHtml='';
  Object.entries(srcCounts).sort((a,b)=>b[1]-a[1]).slice(0,10).forEach(([src,cnt]) => {{
    srcHtml += `<button class="sidebar-item" data-ssrc="${{esc(src)}}">
      <span class="sidebar-item-label" style="font-size:.8rem">${{esc(src)}}</span>
      <span class="sidebar-count">${{cnt}}</span>
    </button>`;
  }});
  sidebarSrc.innerHTML = srcHtml;

  // Sidebar category click
  sidebarCats.querySelectorAll('[data-scat]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      state.cat = btn.dataset.scat;
      document.querySelectorAll('.cat-chip').forEach(c=>c.classList.remove('active'));
      const chip = document.querySelector(`.cat-chip[data-cat="${{CSS.escape(btn.dataset.scat)}}"]`);
      if (chip) chip.classList.add('active'); else {{
        const allChip = document.querySelector('.cat-chip[data-cat="all"]');
        if (allChip) allChip.classList.add('active');
      }}
      render();
    }});
  }});
}}

// ── Init ─────────────────────────────────────────────────────────
function init() {{
  // Stats
  const now = Date.now();
  const todayCnt = ARTICLES.filter(a=>(now-parseDate(a.published))/3.6e6<48).length;
  document.getElementById('statTotal').textContent   = ARTICLES.length;
  document.getElementById('statJa').textContent      = ARTICLES.filter(a=>a.lang==='ja').length;
  document.getElementById('statEn').textContent      = ARTICLES.filter(a=>a.lang==='en').length;
  document.getElementById('statToday').textContent   = todayCnt;

  // Build category chips
  const wrap = document.getElementById('catChips');
  Object.entries(CAT_META).forEach(([name, m]) => {{
    const btn = document.createElement('button');
    btn.className = 'cat-chip';
    btn.dataset.cat = name;
    btn.textContent = m.icon + ' ' + name;
    wrap.appendChild(btn);
  }});

  // Period tabs
  document.querySelectorAll('.period-tab').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.period-tab').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      state.period = btn.dataset.period;
      render();
    }});
  }});

  // Category chips
  wrap.addEventListener('click', e => {{
    const btn = e.target.closest('.cat-chip');
    if (!btn) return;
    document.querySelectorAll('.cat-chip').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    state.cat = btn.dataset.cat;
    render();
  }});

  // Controls
  document.getElementById('langFilter').addEventListener('change', e=>{{ state.lang=e.target.value; render(); }});
  document.getElementById('sortBy').addEventListener('change',     e=>{{ state.sort=e.target.value; render(); }});
  document.getElementById('searchInput').addEventListener('input', e=>{{ state.search=e.target.value.trim(); render(); }});

  render();
}}

document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>'''

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text(html, encoding='utf-8')
    print(f"Dashboard written to {out / 'index.html'} ({(out/'index.html').stat().st_size // 1024} KB)")
