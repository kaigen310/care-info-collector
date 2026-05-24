#!/bin/bash
# セットアップスクリプト — 初回のみ実行

set -e

echo "=== 介護情報収集ツール セットアップ ==="

# Python バージョン確認
python3 --version >/dev/null 2>&1 || { echo "Python3 が見つかりません。インストールしてください。"; exit 1; }

# 仮想環境を作成
if [ ! -d ".venv" ]; then
  echo "仮想環境を作成中..."
  python3 -m venv .venv
fi

# 仮想環境を有効化
source .venv/bin/activate

# ライブラリをインストール
echo "ライブラリをインストール中..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "テスト実行:"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
echo "ダッシュボードを確認:"
echo "  open docs/index.html"
