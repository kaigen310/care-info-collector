# 🏥 介護情報ダッシュボード

介護保険・医療・福祉・施設運営・人材育成・業務改善に関する最新情報を  
**国内外のRSSフィードから毎朝3時に自動収集**し、Webダッシュボードで表示するツール。

**費用ゼロ** — GitHub Actions（無料枠）+ GitHub Pages（無料）で動作。API課金なし。

---

## 機能

| 機能 | 詳細 |
|------|------|
| 自動収集 | 毎朝3:00 JST（PCオフでも動作） |
| 情報源 | 国内10件 + 海外10件のRSSフィード（設定で追加・削除可） |
| AI要約 | 抽出型アルゴリズムで本文から重要文を自動選択（課金なし） |
| 分類 | 7カテゴリに自動分類 |
| ダッシュボード | カテゴリ絞り込み・キーワード検索・スマホ対応 |

### 収集カテゴリ

- 📋 介護保険・制度
- 🏥 医療・健康
- 🤝 福祉・社会保障
- 🏢 施設運営・経営
- 👥 人材育成・HR
- 💡 業務改善・テクノロジー
- 🧠 組織・心理

---

## セットアップ手順

### 1. GitHubリポジトリを作成

1. [GitHub](https://github.com) にログインして **New repository** を作成
2. 名前は `care-info-collector`（任意）
3. **Public** にする（GitHub Pages無料利用に必要）

### 2. このコードをGitHubにプッシュ

```bash
cd /Users/takeru/ツール開発/care-info-collector
git init
git add .
git commit -m "初期コミット"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/care-info-collector.git
git push -u origin main
```

### 3. GitHub Pages を有効化

1. リポジトリの **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / `docs` フォルダを選択 → Save

ダッシュボードURL: `https://YOUR_USERNAME.github.io/care-info-collector/`

### 4. 自動実行を確認

- リポジトリの **Actions** タブを開く
- 手動テスト: "介護情報 日次収集" → **Run workflow**
- 以降は毎朝3:00 JST に自動実行

---

## ローカルでテスト実行

```bash
cd /Users/takeru/ツール開発/care-info-collector
bash setup.sh           # 初回のみ
source .venv/bin/activate
python main.py
open docs/index.html    # ダッシュボードをブラウザで確認
```

---

## 情報源のカスタマイズ

`config/sources.yaml` にRSSフィードを追加・削除できます。

```yaml
feeds:
  - name: サービス名
    url: https://example.com/feed
    lang: ja          # ja または en
    category: 施設運営・経営
```

---

## メール通知（オプション）

Gmailのアプリパスワードを使って、収集完了時にメール通知を受け取れます。

1. Gmailで2段階認証を有効化 → アプリパスワードを生成
2. GitHubリポジトリの **Settings** → **Secrets** → **New secret**:
   - `GMAIL_USER`: yourname@gmail.com
   - `GMAIL_APP_PASSWORD`: 生成したアプリパスワード
   - `NOTIFY_EMAIL`: 通知先メールアドレス
3. `.github/workflows/collect.yml` の `# ── オプション: メール通知` セクションのコメントを外す

---

## ファイル構成

```
care-info-collector/
├── config/sources.yaml      ← RSSフィード一覧（ここを編集）
├── src/
│   ├── collector.py         ← RSSフィード収集
│   ├── scraper.py           ← 記事本文抽出
│   ├── summarizer.py        ← 抽出型要約（API不要）
│   ├── classifier.py        ← カテゴリ分類
│   └── generator.py         ← HTMLダッシュボード生成
├── main.py                  ← メイン実行スクリプト
├── .github/workflows/collect.yml  ← 自動実行設定
└── docs/index.html          ← 生成されるダッシュボード
```
