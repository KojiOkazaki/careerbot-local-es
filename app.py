"""Careerbot Local ES — ローカル専用サーバー

127.0.0.1（このPC自身）でのみ待ち受け、ESの本文や添削結果を外部に送信することはありません。
"""
from __future__ import annotations

import json
import re
import shutil
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import config
import llm
import prompts

APP_VERSION = "0.1.0"
BASE = Path(__file__).resolve().parent
app = FastAPI(title="Careerbot Local ES", docs_url=None, redoc_url=None)

MAX_INPUT_CHARS = 4000


def _sdir(session_id: str) -> Path:
    if not re.fullmatch(r"[0-9]{8}_[0-9]{6}_[0-9a-f]{6}", session_id):
        raise HTTPException(400, "invalid session id")
    return config.DATA_DIR / session_id


def _save(session: dict) -> None:
    if not config.SAVE_HISTORY:
        return
    d = _sdir(session["id"])
    d.mkdir(parents=True, exist_ok=True)
    (d / "session.json").write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "review.md").write_text(review_markdown(session), encoding="utf-8")


def review_markdown(session: dict) -> str:
    inp = session["input"]
    head = [f"# ES添削 {session['created']}", ""]
    meta = [
        f"- 種類：{prompts.ES_TYPES.get(inp.get('es_type', 'auto'))}",
        f"- 設問：{inp.get('question') or '（未入力）'}",
        f"- 文字数制限：{inp.get('char_limit') or '（未入力）'}",
        f"- 応募先：{inp.get('company') or '（未入力）'} / {inp.get('position') or ''}",
    ]
    return "\n".join(head + meta + ["", "## 原文", "", inp.get("text", ""), "", "---", "", session["review"]]) + "\n"


# ---------- 出力後の機械チェック ----------

_SECTION_RE = re.compile(r"(^## 改善点\s*\n)(.*?)(?=^## |\Z)", re.S | re.M)


def _check_and_fix(review: str) -> tuple[str, bool]:
    """改善点の節に「数値化を勧める」「手法名を例示する」記述があれば、その節だけ書き直す"""
    if config.MOCK:
        return review, False
    m = _SECTION_RE.search(review)
    if not m:
        return review, False
    section = m.group(2)
    if not re.search(prompts.NUMERIC_PATTERN, section):
        return review, False
    fixed = llm.chat(prompts.FIX_SYSTEM, "## 改善点\n" + section, temperature=0.0, max_tokens=2000)
    fixed_body = re.sub(r"^## 改善点\s*\n", "", fixed.strip()) + "\n\n"
    return review[: m.start(2)] + fixed_body + review[m.end(2):], True


# ---------- API ----------

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/status")
def api_status():
    l = llm.status()
    sessions = []
    if config.SAVE_HISTORY:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        for p in sorted(config.DATA_DIR.iterdir(), reverse=True):
            f = p / "session.json"
            if f.exists():
                try:
                    s = json.loads(f.read_text(encoding="utf-8"))
                    sessions.append({"id": s["id"], "created": s["created"], "label": s.get("label", "")})
                except Exception:  # noqa: BLE001
                    pass
    return {
        "version": APP_VERSION,
        "mock": config.MOCK,
        "ram_gb": round(llm.ram_gb(), 1),
        "llm": {"backend": config.LLM_BACKEND, **l},
        "prompt_master": prompts.master_path().name,
        "prompt_kind": prompts.master_kind(),
        "data_dir": str(config.DATA_DIR),
        "save_history": config.SAVE_HISTORY,
        "external_endpoints": [],
        "max_input_chars": MAX_INPUT_CHARS,
        "sessions": sessions[:100],
    }


@app.post("/api/review")
async def api_review(body: dict):
    text = (body.get("text") or "").strip()
    if len(text) < 50:
        raise HTTPException(400, "ES本文が短すぎます（50字以上）")
    if len(text) > MAX_INPUT_CHARS:
        raise HTTPException(400, f"ES本文が長すぎます（{MAX_INPUT_CHARS}字以内）")
    data = {
        "es_type": body.get("es_type", "auto"),
        "question": (body.get("question") or "").strip(),
        "char_limit": (str(body.get("char_limit") or "")).strip(),
        "company": (body.get("company") or "").strip(),
        "position": (body.get("position") or "").strip(),
        "grade": (body.get("grade") or "").strip(),
        "memo": (body.get("memo") or "").strip(),
        "text": text,
    }
    try:
        review = await run_in_threadpool(
            llm.chat, prompts.system_prompt(), prompts.user_prompt(data), config.TEMPERATURE, config.MAX_OUTPUT_TOKENS
        )
        review, fixed = await run_in_threadpool(_check_and_fix, review)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"添削に失敗しました（Ollamaに接続できていますか）: {e}")

    session = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6],
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "label": " / ".join(x for x in [prompts.ES_TYPES.get(data["es_type"], ""), data["company"], text[:20] + "…"] if x),
        "input": data,
        "review": review,
        "model": llm.model_name(),
        "prompt_kind": prompts.master_kind(),
        "auto_fixed": fixed,
    }
    _save(session)
    return session


@app.get("/api/sessions/{session_id}")
def api_get_session(session_id: str):
    p = _sdir(session_id) / "session.json"
    if not p.exists():
        raise HTTPException(404, "not found")
    return json.loads(p.read_text(encoding="utf-8"))


@app.delete("/api/sessions/{session_id}")
def api_delete_session(session_id: str):
    d = _sdir(session_id)
    if d.exists():
        shutil.rmtree(d)
    return {"ok": True}


@app.delete("/api/sessions")
def api_delete_all():
    if config.DATA_DIR.exists():
        for p in config.DATA_DIR.iterdir():
            if (p / "session.json").exists():
                shutil.rmtree(p)
    return {"ok": True}


app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def main():
    if config.SAVE_HISTORY:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    url = f"http://{config.HOST}:{config.PORT}"
    print("=" * 60)
    print(f" Careerbot Local ES {APP_VERSION}")
    print(f" 画面: {url}  （このPCの中だけで動いています）")
    print(f" 添削プロンプト: {'正式版' if prompts.master_kind() == 'full' else '簡易版（公開）'} {prompts.master_path().name}")
    print(f" 保存先: {config.DATA_DIR if config.SAVE_HISTORY else '（保存しない設定）'}")
    if config.MOCK:
        print(" ※ MOCKモード: LLM は使いません")
    print("=" * 60)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="warning")


if __name__ == "__main__":
    main()
