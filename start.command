#!/bin/bash
# Careerbot Local ES 起動スクリプト（Mac）
# Finderでダブルクリックするか、ターミナルで ./start.command
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 が見つかりません。https://www.python.org/downloads/ からインストールしてください。"
  read -p "Enterで閉じます"; exit 1
fi

if [ ! -d .venv ]; then
  echo "初回セットアップ中（数分かかります）..."
  python3 -m venv .venv || { echo "仮想環境の作成に失敗しました"; read -p "Enterで閉じます"; exit 1; }
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt || { echo "ライブラリのインストールに失敗しました"; read -p "Enterで閉じます"; exit 1; }

python app.py
