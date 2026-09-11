# Careerbot Local ES

大学キャリアセンターの職員向け、**完全ローカルのES添削支援ツール**です。
学生のエントリーシート（ガクチカ・自己PR・志望動機など）を貼り付けると、このPCの中だけで **評価 → 評価の内訳 → 良い点 → 改善点（原文引用付き）→ 面接想定質問 → 学生に確認すること** を作ります。本文は代筆せず、直す場所と本人が考えるべき問いを返します。

- ESの本文・添削結果は **外部に一切送信しません**
- 利用料・API料金は **かかりません**
- 無償・無保証・サポートなし（下記「利用条件」参照）
- 姉妹ツール：[Careerbot Local Note](https://github.com/KojiOkazaki/careerbot-local-note)（面談の相談記録）／[Careerbot Local Interview Note](https://github.com/KojiOkazaki/careerbot-local-interview-note)（模擬面接の記録・フィードバック）
- 同梱の添削プロンプトは **簡易版**（基本の観点のみ）です。X版・LINE版キャリアボットで運用している正式版（種類別の詳細チェック観点・面接深掘り観点）は有償で提供しています（[prompts/README.md](prompts/README.md)）

> **重要**：添削結果はAIの下書きです。必ず職員が読んで判断し、学生に渡す言葉を選んでください。ESには学生の個人情報が含まれます。貼り付け前に氏名等を消し、履歴の保管・削除は所属大学の規程に従ってください。

## 職員モードの出力

| 見出し | 内容 | 学生向けコピー |
|---|---|---|
| 種類の判定 | ガクチカ／自己PR／志望動機／その他 | 含む |
| 総合評価 | S（提出可）／A（一部補強）／B（構成・中身の補強）／C（書き直し）＋2〜3文 | 含む |
| 評価の内訳 | 設問への回答／構成／論理性／具体性／説得力／表現 を ◎○△ と原文の根拠で | 含む |
| 良い点 | 原文引用つき | 含む |
| 改善点 | 優先度順3〜5点。原文引用 → なぜ → 何を書き足すか（本人が考える箇所は空欄で示す） | 含む |
| 面接で聞かれそうなこと | 3〜5問 | 含む |
| 学生に確認すること | ESの不足情報／自己分析の問い／面接準備の問い、の3区分 | **含まない**（職員用） |

修正案（本人の語句だけで並べ替えた全文）が必要な場合は `config.py` の `INCLUDE_REWRITE = True` にします。標準では出しません。

「学生向けにコピー」ボタンは「学生に確認すること」を除いた本文をコピーします。

## 動作環境

| | 推奨 | 最低 |
|---|---|---|
| OS | macOS（Apple Silicon） | macOS（Intel）／Windows 11（動作未確認） |
| メモリ | 16GB | 8GB |
| ブラウザ | Google Chrome | Edge でも可 |

Whisper（音声）は使わないため、[Careerbot Local Note](https://github.com/KojiOkazaki/careerbot-local-note) より軽く、Ollama とモデルだけあれば動きます。Local Note を導入済みなら手順1〜3は不要です。

## セットアップ（初回のみ）

1. **Ollama をインストール**：https://ollama.com からダウンロードして起動
2. **LLM を取得**：ターミナル（Windows は PowerShell）で。メモリ16GB以上は `gemma4:e4b`、8GBは `gemma3:4b`
   ```
   ollama pull gemma4:e4b
   ```
3. **Python 3.10 以上**：https://www.python.org/downloads/（Windows は「Add python.exe to PATH」にチェック）
4. **本ツールをダウンロードして起動**

   Mac（ターミナルに丸ごと貼り付け）：
   ```
   cd ~/Downloads
   curl -L -o les.zip https://github.com/KojiOkazaki/careerbot-local-es/archive/refs/heads/main.zip
   unzip -q -o les.zip -d ~/Documents
   cd ~/Documents/careerbot-local-es-main
   chmod +x start.command && ./start.command
   ```
   Windows（PowerShell に丸ごと貼り付け）：
   ```
   Invoke-WebRequest -Uri https://github.com/KojiOkazaki/careerbot-local-es/archive/refs/heads/main.zip -OutFile $env:TEMP\les.zip
   Expand-Archive -Path $env:TEMP\les.zip -DestinationPath C:\LocalES -Force
   Set-Location C:\LocalES\careerbot-local-es-main
   .\start.bat
   ```
5. Chrome で `http://127.0.0.1:8766` が開きます。左の「準備の確認」がすべて ✓ ならOK

2回目以降は `start.command`（Mac）／`start.bat`（Windows）をダブルクリック。Local Note と同時に起動できます（ポートが違います）。

## 使い方

1. 種類（自動判定でも可）・文字数制限・応募先・設問文を入れる
2. ES本文を貼る（**学生の氏名など不要な個人情報は消す**）。文字数と制限超過がその場で表示されます
3. 面談で本人が話した情報があれば「職員からの補足」に入れる（修正案に使われます）
4. 「添削する」→ 1〜3分待つ
5. 結果を読み、「学生向けにコピー」で学生に渡す文章の下書きを取る。必要なら編集
6. 「Markdownを保存」で控えを残す／「削除」でPCから消す

## データの扱い

| データ | 保存場所 | 外部送信 |
|---|---|---|
| ES本文・添削結果 | `~/CareerbotLocalES/日時のフォルダ/`（`config.py` の `SAVE_HISTORY = False` で保存しない設定に） | しない |
| 利用状況・ログ | 収集しない | しない |

通信が発生するのは Ollama によるモデルの初回ダウンロードと、初回セットアップ時のPythonライブラリ取得のみ。情報システム部門向けの詳細は [docs/SECURITY.md](docs/SECURITY.md)。

## よくあるトラブル

- **Ollama：接続できません** → Ollama を起動する
- **LLM：（未取得）** → `ollama pull gemma4:e4b`（8GBは `gemma3:4b`）。別モデルは `config.py` の `LLM_MODEL`
- **添削に失敗しました／途中で止まる** → メモリ不足。他アプリを閉じる、または `LLM_MODEL = "gemma3:4b"`
- **評価が同じESで毎回変わる** → `config.py` の `TEMPERATURE` を 0.1 に下げる
- **原文に無い内容が書かれる** → 起こりえます。必ず原文と照合し、本人に書かせる形（空欄と「学生に確認すること」）で返してください
- **Address already in use** → すでに起動しています
- Mac「開発元を確認できないため開けません」→ 右クリック→開く／Windows「PCが保護されました」→ 詳細情報→実行

Local Note の [導入マニュアル](https://github.com/KojiOkazaki/careerbot-local-note/blob/main/docs/MANUAL.md) の手順・エラー対処は本ツールにもほぼそのまま当てはまります。

## カスタマイズ

- `prompts/es_review_lite.md`：同梱の簡易版プロンプト。観点を変えるならここ。正式版を `prompts/es_review.md` に置くと自動で優先されます
- `prompts.py` の `STAFF_FORMAT`：職員向けの出力形式（見出し・評価基準・評価の内訳の観点）。`INCLUDE_REWRITE` で修正案の有無
- `config.py`：モデル・温度・保存先・履歴の有無

## 利用条件

- ライセンス：MIT（[LICENSE](LICENSE)）。無償・無保証
- **サポートは行いません**。Issueは受け付けていません。質問は Discussions へ
- 重大なセキュリティ上の問題のみ、修正を検討します
- 使用モデルのライセンス：Gemma 4（Apache 2.0, Google）／Gemma 3（Gemma Terms of Use）

正式版の添削プロンプト、複数職員での運用、学生が直接使える版、設定・研修・保守が必要な大学向けには有償版があります。https://careerbot.tokyo

---
CAREERBOT Inc. / 東京都立産業技術大学院大学 岡崎浩二
