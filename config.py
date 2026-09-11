"""Careerbot Local ES 設定ファイル

変更が必要そうな項目はすべてここにあります。コードを触る必要はありません。
"""
import os
from pathlib import Path

# ---- 画面（Chromeで開くアドレス）----
HOST = "127.0.0.1"          # このPC以外からは接続できません
PORT = 8766                 # Local Note(8765) と同時に動かせます

# ---- LLM（添削）----
# "ollama"（推奨）または "lmstudio"
LLM_BACKEND = "ollama"
OLLAMA_URL = "http://127.0.0.1:11434"
LMSTUDIO_URL = "http://127.0.0.1:1234/v1"

# "auto" にすると、このPCのメモリ量で自動選択します
#   メモリ 12GB 未満 → gemma3:4b    （3.3GB。8GBのPC向け）
#   メモリ 12GB 以上 → gemma4:e4b   （9.6GB。16GBのPC向け）
#   32GB 以上なら "gemma4:12b" も候補（添削の質が上がります）
LLM_MODEL = "auto"

# True にすると出力の最後に「修正案」（本人の語句だけで並べ替えた全文）を付けます。
# 標準は False（代筆せず、直す場所と本人への問いだけを返す）
INCLUDE_REWRITE = False

# 添削のブレを抑えるため低めに。上げると表現が多様になります
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 4000

# ---- 保存 ----
# 添削履歴の保存先（このPC内）。ESは学生の個人情報を含むため、大学の規程に従って管理してください
DATA_DIR = Path(os.environ.get("LOCAL_ES_DATA_DIR", Path.home() / "CareerbotLocalES"))
# False にすると履歴を一切残しません（画面を閉じたら消えます）
SAVE_HISTORY = True

# ---- 開発用 ----
# LOCAL_ES_MOCK=1 で起動すると、LLM無しで画面を確認できます
MOCK = os.environ.get("LOCAL_ES_MOCK") == "1"
