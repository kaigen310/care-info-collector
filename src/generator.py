"""Static HTML dashboard generator — digest-first, database-style."""

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

    # Build category meta JSON for JS
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
/* ── Reset & Tokens ─────────────────────────────── */
:root {{
  --bg: #f0f4f8;
  --surface: #ffffff;
  --surface2: #f8fafc;
  --border: #dde3ea;
  --text: #1a2433;
  --muted: #5a6a7e;
  --accent: #1565c0;
  --accent-light: #e8f0fe;
  --good: #1b8a4a;
  --warn: #b45309;
  --radius: 10px;
  --shadow: 0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.05);
  --shadow-md: 0 4px 14px rgba(0,0,0,.10);
  --font: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Yu Gothic UI", sans-serif;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #1c2330;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --accent: #58a6ff;
    --accent-light: #1a2a45;
  }}
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
button {{ font-family: var(--font); cursor: pointer; }}

/* ── Topbar ──────────────────────────────────────── */
.topbar {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: .75rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  position: sticky;
  top: 0;
  z-index: 200;
  box-shadow: var(--shadow);
}}
.topbar-logo {{ font-size: 1.05rem; font-weight: 700; white-space: nowrap; }}
.topbar-logo span {{ color: var(--accent); }}
.search-wrap {{ flex: 1; min-width: 180px; max-width: 380px; position: relative; }}
.search-wrap svg {{ position: absolute; left: .7rem; top: 50%; transform: translateY(-50%); color: var(--muted); }}
.search-input {{
  width: 100%; padding: .45rem .9rem .45rem 2.2rem;
  border: 1px solid var(--border); border-radius: 9999px;
  background: var(--bg); color: var(--text); font-size: .9rem; outline: none;
  transition: border-color .2s;
}}
.search-input:focus {{ border-color: var(--accent); }}
.topbar-updated {{ font-size: .75rem; color: var(--muted); margin-left: auto; white-space: nowrap; }}

/* ── Stats bar ───────────────────────────────────── */
.statsbar {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: .55rem 1.5rem;
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  align-items: center;
  font-size: .82rem;
  color: var(--muted);
}}
.statsbar strong {{ color: var(--text); font-size: 1rem; }}
.stat-pill {{
  display: flex; align-items: center; gap: .3rem;
  padding: .2rem .65rem; border-radius: 9999px;
  background: var(--surface2); border: 1px solid var(--border);
}}
#resultCount {{ font-size: .82rem; color: var(--muted); margin-left: auto; }}

/* ── Controls ────────────────────────────────────── */
.controls {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 1.5rem;
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
}}

/* Time tabs */
.time-tabs {{ display: flex; gap: 0; flex-shrink: 0; }}
.time-tab {{
  padding: .65rem 1rem;
  border: none; border-bottom: 2px solid transparent;
  background: transparent; color: var(--muted);
  font-size: .88rem; font-weight: 500;
  transition: color .15s, border-color .15s;
  white-space: nowrap;
}}
.time-tab:hover {{ color: var(--text); }}
.time-tab.active {{ color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }}

.controls-sep {{ width: 1px; background: var(--border); margin: .5rem 0; flex-shrink: 0; }}

/* Category chips */
.cat-chips {{ display: flex; gap: .4rem; padding: .5rem 0 .5rem .75rem; overflow-x: auto; align-items: center; flex: 1; }}
.cat-chip {{
  padding: .28rem .75rem; border-radius: 9999px;
  border: 1px solid var(--border); background: var(--surface2);
  color: var(--muted); font-size: .8rem; white-space: nowrap;
  transition: all .15s;
}}
.cat-chip:hover {{ border-color: currentColor; }}
.cat-chip.active {{ background: var(--accent); color: #fff; border-color: transparent; }}

/* Right controls */
.right-controls {{
  display: flex; align-items: center; gap: .5rem;
  padding: .5rem 0 .5rem .75rem; flex-shrink: 0;
}}
.ctrl-select {{
  padding: .3rem .65rem; border-radius: 6px;
  border: 1px solid var(--border); background: var(--surface2);
  color: var(--text); font-size: .82rem; outline: none; cursor: pointer;
}}

/* ── Main Layout ─────────────────────────────────── */
.main-wrap {{ display: flex; gap: 0; max-width: 1200px; margin: 0 auto; padding: 1.25rem 1rem; }}
.sidebar {{
  width: 220px; flex-shrink: 0; margin-right: 1.25rem;
  position: sticky; top: 120px; align-self: flex-start;
}}
.sidebar-section {{ margin-bottom: 1rem; }}
.sidebar-title {{ font-size: .72rem; font-weight: 700; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; margin-bottom: .5rem; }}
.sidebar-item {{
  display: flex; align-items: center; justify-content: space-between;
  padding: .35rem .6rem; border-radius: 6px; border: none;
  background: transparent; color: var(--text); font-size: .84rem;
  width: 100%; text-align: left; cursor: pointer; transition: background .15s;
}}
.sidebar-item:hover {{ background: var(--surface); }}
.sidebar-item.active {{ background: var(--accent-light); color: var(--accent); font-weight: 600; }}
.sidebar-count {{
  font-size: .74rem; padding: 1px 6px; border-radius: 9999px;
  background: var(--surface2); color: var(--muted);
}}
.sidebar-item.active .sidebar-count {{ background: var(--accent); color: #fff; }}

.articles-col {{ flex: 1; min-width: 0; }}

/* ── Article Card (digest-first) ─────────────────── */
.article-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: .85rem;
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: box-shadow .2s;
}}
.article-card:hover {{ box-shadow: var(--shadow-md); }}

.card-header {{
  display: flex; align-items: flex-start; justify-content: space-between;
  flex-wrap: wrap; gap: .4rem;
  padding: .7rem 1rem .55rem;
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
}}
.card-cats {{ display: flex; flex-wrap: wrap; gap: .3rem; flex: 1; }}
.cat-badge {{
  font-size: .72rem; padding: 2px 9px; border-radius: 9999px;
  font-weight: 600; white-space: nowrap;
}}
.card-meta2 {{
  display: flex; align-items: center; gap: .5rem;
  font-size: .76rem; color: var(--muted); flex-shrink: 0;
}}
.lang-badge {{
  font-size: .68rem; padding: 1px 5px; border-radius: 4px; font-weight: 700;
}}
.lang-ja {{ background: #fef9c3; color: #854d0e; }}
.lang-en {{ background: #dbeafe; color: #1e40af; }}
.translated-badge {{
  font-size: .68rem; padding: 1px 6px; border-radius: 4px;
  background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0;
  font-weight: 600;
}}
.age-badge {{
  font-size: .72rem; padding: 2px 7px; border-radius: 9999px;
  font-weight: 600;
}}
.age-today {{ background: #dcfce7; color: #166534; }}
.age-week  {{ background: #fef9c3; color: #854d0e; }}
.age-old   {{ background: var(--surface2); color: var(--muted); }}

/* Summary section — this is the hero */
.card-digest {{
  padding: .85rem 1.1rem .7rem;
}}
.card-summary-text {{
  font-size: .97rem;
  line-height: 1.75;
  color: var(--text);
  margin-bottom: .7rem;
}}
.card-no-summary {{
  font-size: .85rem;
  color: var(--muted);
  font-style: italic;
  padding: .3rem 0;
  margin-bottom: .5rem;
}}

/* Title + link below summary */
.card-footer {{
  padding: .5rem 1.1rem .7rem;
  border-top: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: .5rem;
}}
.card-source-line {{ font-size: .78rem; color: var(--muted); }}
.card-title-link {{
  font-size: .88rem; font-weight: 600; color: var(--text);
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}}
.card-title-link:hover {{ color: var(--accent); text-decoration: none; }}
.read-link {{
  font-size: .82rem; font-weight: 600; color: var(--accent);
  white-space: nowrap; flex-shrink: 0;
  border: 1px solid var(--accent);
  padding: .25rem .75rem; border-radius: 6px;
  transition: background .15s, color .15s;
}}
.read-link:hover {{ background: var(--accent); color: #fff; text-decoration: none; }}

/* ── Section headers (category grouping) ─────────── */
.section-header {{
  display: flex; align-items: center; gap: .6rem;
  margin: 1.2rem 0 .7rem;
  padding-bottom: .5rem;
  border-bottom: 2px solid var(--border);
}}
.section-icon {{ font-size: 1.1rem; }}
.section-name {{ font-size: 1rem; font-weight: 700; color: var(--text); }}
.section-count {{
  font-size: .78rem; padding: 2px 8px; border-radius: 9999px;
  background: var(--surface2); border: 1px solid var(--border); color: var(--muted);
}}

/* ── Empty state ─────────────────────────────────── */
.empty-state {{
  text-align: center; padding: 3rem 1rem; color: var(--muted);
  font-size: .95rem; display: none;
}}

/* ── Responsive ──────────────────────────────────── */
@media (max-width: 720px) {{
  .sidebar {{ display: none; }}
  .main-wrap {{ padding: .75rem .5rem; }}
  .topbar {{ padding: .6rem .75rem; }}
  .controls {{ padding: 0 .75rem; }}
  .statsbar {{ padding: .5rem .75rem; }}
}}
</style>
</head>
<body>

<!-- Topbar -->
<header class="topbar">
  <div class="topbar-logo">🏥 介護<span>情報</span>DB</div>
  <div class="search-wrap">
    <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
    </svg>
    <input class="search-input" type="search" id="searchInput" placeholder="キーワードで絞り込む…" />
  </div>
  <div class="topbar-updated">最終更新: {updated_at}</div>
</header>

<!-- Stats bar -->
<div class="statsbar">
  <div class="stat-pill"><strong id="statTotal">—</strong>&nbsp;件</div>
  <div class="stat-pill">🇯🇵 国内 <strong id="statJa">—</strong></div>
  <div class="stat-pill">🌐 海外 <strong id="statEn">—</strong></div>
  <div class="stat-pill">🆕 今日 <strong id="statToday">—</strong></div>
  <div id="resultCount">表示中: <strong id="visibleCount">—</strong> 件</div>
</div>

<!-- Controls -->
<div class="controls">
  <div class="time-tabs">
    <button class="time-tab" data-period="today">🆕 今日</button>
    <button class="time-tab" data-period="week">今週</button>
    <button class="time-tab" data-period="month">今月</button>
    <button class="time-tab active" data-period="all">すべて</button>
  </div>
  <div class="controls-sep"></div>
  <div class="cat-chips" id="catChips">
    <button class="cat-chip active" data-cat="all">すべて</button>
  </div>
  <div class="controls-sep"></div>
  <div class="right-controls">
    <select class="ctrl-select" id="langFilter">
      <option value="all">🌐 全言語</option>
      <option value="ja">🇯🇵 日本語</option>
      <option value="en">🇺🇸 English</option>
    </select>
    <select class="ctrl-select" id="sortBy">
      <option value="date">新着順</option>
      <option value="cat">カテゴリ順</option>
    </select>
  </div>
</div>

<!-- Main -->
<div class="main-wrap">

  <!-- Sidebar category counts -->
  <aside class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-title">カテゴリ</div>
      <div id="sidebarCats"></div>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-title">情報源</div>
      <div id="sidebarSources"></div>
    </div>
  </aside>

  <!-- Articles column -->
  <div class="articles-col">
    <div id="articlesContainer"></div>
    <div class="empty-state" id="emptyState">
      条件に一致する記事がありませんでした。<br>検索語・カテゴリ・期間を変更してみてください。
    </div>
  </div>

</div>

<script>
// ── Data ────────────────────────────────────────────────────────
const ARTICLES = {articles_json};
const CAT_META = {cat_meta_json};
const DEFAULT_COLOR = '#6B7280';

// ── State ───────────────────────────────────────────────────────
let state = {{
  period: 'all',
  cat: 'all',
  lang: 'all',
  sort: 'date',
  search: '',
}};

// ── Helpers ─────────────────────────────────────────────────────
function esc(s) {{
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function parseDate(s) {{
  if (!s) return new Date(0);
  // "YYYY-MM-DD HH:mm" or "YYYY-MM-DD"
  return new Date(s.replace(' ', 'T') + (s.length === 10 ? 'T00:00:00+09:00' : '+09:00'));
}}

function ageBucket(dateStr) {{
  const now = Date.now();
  const d = parseDate(dateStr).getTime();
  const hours = (now - d) / 3600000;
  if (hours < 48)   return 'today';
  if (hours < 168)  return 'week';
  return 'old';
}}

function ageBadge(dateStr) {{
  const b = ageBucket(dateStr);
  const d = parseDate(dateStr);
  const hours = (Date.now() - d.getTime()) / 3600000;
  let label, cls;
  if (hours < 24)        {{ label = '今日'; cls = 'age-today'; }}
  else if (hours < 48)   {{ label = '昨日'; cls = 'age-today'; }}
  else if (hours < 168)  {{ label = Math.floor(hours/24) + '日前'; cls = 'age-week'; }}
  else                   {{ label = d.toLocaleDateString('ja-JP', {{month:'short', day:'numeric'}}); cls = 'age-old'; }}
  return `<span class="age-badge ${{cls}}">${{label}}</span>`;
}}

function catBadges(cats) {{
  return (cats || []).map(c => {{
    const m = CAT_META[c] || {{color: DEFAULT_COLOR, icon: '📰'}};
    const col = m.color;
    return `<span class="cat-badge" style="background:${{col}}20;color:${{col}};border:1px solid ${{col}}40">${{m.icon}} ${{esc(c)}}</span>`;
  }}).join('');
}}

function buildCard(a) {{
  const hasSummary = a.summary && a.summary.trim().length > 50;
  // 英語記事は翻訳済みテキストを優先表示
  const displaySummary = (a.lang === 'en' && a.summary_ja) ? a.summary_ja : (a.summary || '');
  const digestHtml = `<p class="card-summary-text">${{esc(displaySummary)}}</p>`;

  const langBadge = a.lang === 'ja'
    ? '<span class="lang-badge lang-ja">日本語</span>'
    : '<span class="lang-badge lang-en">English</span>';

  // タイトルも翻訳済みを優先
  const displayTitle = (a.lang === 'en' && a.title_ja) ? a.title_ja : (a.title || '');
  // 英語記事には自動翻訳バッジを表示
  const translatedBadge = (a.lang === 'en')
    ? '<span class="translated-badge">🌐 自動翻訳</span>'
    : '';

  return `
<div class="article-card"
  data-cats="${{esc(JSON.stringify(a.categories||[]))}}"
  data-lang="${{a.lang||'ja'}}"
  data-date="${{a.published||''}}"
  data-source="${{esc(a.source||'')}}"
  data-search="${{esc(((a.title_ja||a.title)+' '+(a.summary_ja||a.summary||'')+' '+a.source).toLowerCase())}}">
  <div class="card-header">
    <div class="card-cats">${{catBadges(a.categories)}}</div>
    <div class="card-meta2">
      ${{ageBadge(a.published)}}
      ${{translatedBadge}}
      ${{langBadge}}
    </div>
  </div>
  <div class="card-digest">
    ${{digestHtml}}
  </div>
  <div class="card-footer">
    <div>
      <div class="card-source-line">${{esc(a.source)}} &nbsp;·&nbsp; ${{(a.published||'').slice(0,10)}}</div>
      <a class="card-title-link" href="${{esc(a.url)}}" target="_blank" rel="noopener">${{esc(displayTitle)}}</a>
    </div>
    <a class="read-link" href="${{esc(a.url)}}" target="_blank" rel="noopener">記事を読む →</a>
  </div>
</div>`;
}}

// ── Filtering & Sorting ─────────────────────────────────────────
function filterArticles() {{
  const now = Date.now();
  return ARTICLES.filter(a => {{
    // Period
    if (state.period !== 'all') {{
      const hours = (now - parseDate(a.published).getTime()) / 3600000;
      if (state.period === 'today' && hours > 48)  return false;
      if (state.period === 'week'  && hours > 168) return false;
      if (state.period === 'month' && hours > 720) return false;
    }}
    // Category
    if (state.cat !== 'all' && !(a.categories||[]).includes(state.cat)) return false;
    // Language
    if (state.lang !== 'all' && a.lang !== state.lang) return false;
    // Search
    if (state.search) {{
      const q = state.search.toLowerCase();
      const hay = (a.title + ' ' + (a.summary||'') + ' ' + a.source).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }}).sort((a, b) => {{
    if (state.sort === 'date') return parseDate(b.published) - parseDate(a.published);
    // Category sort: group by first category
    const ca = (a.categories||[''])[0] || '';
    const cb = (b.categories||[''])[0] || '';
    if (ca !== cb) return ca.localeCompare(cb, 'ja');
    return parseDate(b.published) - parseDate(a.published);
  }});
}}

// ── Rendering ───────────────────────────────────────────────────
function renderCatSection(catName, articles) {{
  const m = CAT_META[catName] || {{color: DEFAULT_COLOR, icon: '📰'}};
  const col = m.color;
  const cards = articles.map(buildCard).join('');
  return `
<div class="section-header">
  <span class="section-icon">${{m.icon}}</span>
  <span class="section-name" style="color:${{col}}">${{esc(catName)}}</span>
  <span class="section-count">${{articles.length}}件</span>
</div>
${{cards}}`;
}}

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

  if (state.sort === 'cat' && state.cat === 'all') {{
    // Group by category
    const groups = {{}};
    const CAT_ORDER = Object.keys(CAT_META);
    filtered.forEach(a => {{
      const cat = (a.categories||[])[0] || '未分類';
      (groups[cat] = groups[cat] || []).push(a);
    }});
    let html = '';
    CAT_ORDER.forEach(cat => {{
      if (groups[cat]?.length) html += renderCatSection(cat, groups[cat]);
    }});
    if (groups['未分類']?.length) html += renderCatSection('未分類', groups['未分類']);
    container.innerHTML = html;
  }} else {{
    container.innerHTML = filtered.map(buildCard).join('');
  }}

  renderSidebar(filtered);
}}

// ── Sidebar ─────────────────────────────────────────────────────
function renderSidebar(filtered) {{
  // Category counts
  const catCounts = {{}};
  filtered.forEach(a => {{
    (a.categories||[]).forEach(c => {{ catCounts[c] = (catCounts[c]||0)+1; }});
  }});

  const sidebarCats = document.getElementById('sidebarCats');
  let catHtml = `<button class="sidebar-item ${{state.cat==='all'?'active':''}}" data-scat="all">
    <span>すべて</span><span class="sidebar-count">${{filtered.length}}</span>
  </button>`;
  Object.entries(catCounts).sort((a,b)=>b[1]-a[1]).forEach(([cat, cnt]) => {{
    const m = CAT_META[cat] || {{icon:'📰'}};
    const active = state.cat === cat ? 'active' : '';
    catHtml += `<button class="sidebar-item ${{active}}" data-scat="${{esc(cat)}}">
      <span>${{m.icon}} ${{esc(cat)}}</span><span class="sidebar-count">${{cnt}}</span>
    </button>`;
  }});
  sidebarCats.innerHTML = catHtml;

  // Source counts
  const srcCounts = {{}};
  filtered.forEach(a => {{ srcCounts[a.source] = (srcCounts[a.source]||0)+1; }});
  const sidebarSrc = document.getElementById('sidebarSources');
  let srcHtml = '';
  Object.entries(srcCounts).sort((a,b)=>b[1]-a[1]).slice(0, 10).forEach(([src, cnt]) => {{
    srcHtml += `<button class="sidebar-item" data-ssrc="${{esc(src)}}">
      <span style="font-size:.8rem">${{esc(src)}}</span><span class="sidebar-count">${{cnt}}</span>
    </button>`;
  }});
  sidebarSrc.innerHTML = srcHtml;

  // Bind sidebar events
  sidebarCats.querySelectorAll('[data-scat]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      state.cat = btn.dataset.scat;
      document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
      const chip = document.querySelector(`.cat-chip[data-cat="${{btn.dataset.scat}}"]`);
      if (chip) chip.classList.add('active');
      render();
    }});
  }});
}}

// ── Init ─────────────────────────────────────────────────────────
function init() {{
  const now = Date.now();
  const todayCnt = ARTICLES.filter(a => (now - parseDate(a.published).getTime())/3600000 < 48).length;
  const jaCnt = ARTICLES.filter(a => a.lang === 'ja').length;
  const enCnt = ARTICLES.filter(a => a.lang === 'en').length;
  document.getElementById('statTotal').textContent = ARTICLES.length;
  document.getElementById('statJa').textContent = jaCnt;
  document.getElementById('statEn').textContent = enCnt;
  document.getElementById('statToday').textContent = todayCnt;

  // Build category chips
  const chips = document.getElementById('catChips');
  Object.entries(CAT_META).forEach(([name, m]) => {{
    const btn = document.createElement('button');
    btn.className = 'cat-chip';
    btn.dataset.cat = name;
    btn.style.setProperty('--cc', m.color);
    btn.textContent = m.icon + ' ' + name;
    chips.appendChild(btn);
  }});

  // Events: time tabs
  document.querySelectorAll('.time-tab').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.time-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.period = btn.dataset.period;
      render();
    }});
  }});

  // Events: category chips
  document.getElementById('catChips').addEventListener('click', e => {{
    const btn = e.target.closest('.cat-chip');
    if (!btn) return;
    document.querySelectorAll('.cat-chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.cat = btn.dataset.cat;
    render();
  }});

  // Events: controls
  document.getElementById('langFilter').addEventListener('change', e => {{
    state.lang = e.target.value; render();
  }});
  document.getElementById('sortBy').addEventListener('change', e => {{
    state.sort = e.target.value; render();
  }});
  document.getElementById('searchInput').addEventListener('input', e => {{
    state.search = e.target.value.trim();
    render();
  }});

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
