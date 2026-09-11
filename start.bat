@echo off
rem Careerbot Local ES 起動スクリプト（Windows・動作未確認）
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3 が見つかりません。python.org からインストールしてください。& pause & exit /b 1)
if not exist .venv (
  echo 初回セットアップ中（数分かかります）...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q --upgrade pip
pip install -q -r requirements.txt || (echo ライブラリのインストールに失敗しました & pause & exit /b 1)
python app.py
pause
