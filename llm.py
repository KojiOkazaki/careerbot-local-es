"""ローカルLLM（Ollama / LM Studio）への接続

ES添削はすべてこのPC内のLLMで処理します。
"""
from __future__ import annotations

import requests

import config


def ram_gb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except Exception:
        return 0.0


def model_name() -> str:
    if config.LLM_MODEL != "auto":
        return config.LLM_MODEL
    if config.LLM_BACKEND == "lmstudio":
        return "google/gemma-4-e4b"
    return "gemma3:4b" if ram_gb() < 12 else "gemma4:e4b"


def _base() -> str:
    return config.OLLAMA_URL if config.LLM_BACKEND == "ollama" else config.LMSTUDIO_URL


def status() -> dict:
    """接続状態とモデルの有無を返す"""
    if config.MOCK:
        return {"connected": True, "model": model_name(), "model_available": True, "models": [model_name()]}
    info = {"connected": False, "model": model_name(), "model_available": False, "models": []}
    try:
        if config.LLM_BACKEND == "ollama":
            r = requests.get(f"{_base()}/api/tags", timeout=3)
            r.raise_for_status()
            names = [m["name"] for m in r.json().get("models", [])]
        else:
            r = requests.get(f"{_base()}/models", timeout=3)
            r.raise_for_status()
            names = [m["id"] for m in r.json().get("data", [])]
        info["connected"] = True
        info["models"] = names
        want = model_name()
        info["model_available"] = any(n == want or n.split(":")[0] == want for n in names)
    except Exception:
        pass
    return info


def chat(system: str, user: str, temperature: float = 0.3, max_tokens: int = 4000) -> str:
    if config.MOCK:
        return _mock_reply(system)
    if config.LLM_BACKEND == "ollama":
        return _ollama(system, user, temperature, max_tokens)
    return _lmstudio(system, user, temperature, max_tokens)


def _ollama(system: str, user: str, temperature: float, max_tokens: int) -> str:
    body = {
        "model": model_name(),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    # 思考モードがあるモデルはオフにする（オンだと数倍遅い）。非対応モデルなら外して再送
    r = requests.post(f"{_base()}/api/chat", json={**body, "think": False}, timeout=1800)
    if r.status_code == 400:
        r = requests.post(f"{_base()}/api/chat", json=body, timeout=1800)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def _lmstudio(system: str, user: str, temperature: float, max_tokens: int) -> str:
    body = {
        "model": model_name(),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    r = requests.post(f"{_base()}/chat/completions", json=body, timeout=1800)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _mock_reply(system: str) -> str:
    return (
        "## 種類の判定\nガクチカとして拝見しました。アルバイトでの後輩指導の経験です。\n\n"
        "## 総合評価\n**A**\n具体的な行動が書けており説得力があります。最も大きな課題は、取り組んだ動機が読めないことです。\n\n"
        "## 評価の内訳\n| 観点 | 評価 | 根拠（原文から） |\n|---|---|---|\n"
        "| 設問への回答 | ◎ | 「最も力を入れたのは」 |\n| 構成 | ○ | 結論が2文目 |\n| 論理性 | ○ | 課題→行動はあるが動機が無い |\n"
        "| 具体性 | ◎ | 「困っている点を確認し」 |\n| 説得力 | ○ | 結果が「安定した」のみ |\n| 表現 | ◎ | 記述なし |\n\n"
        "## 良い点\n- 「一方的に教えるのではなく」— 行動の転換点が明確です\n\n"
        "## 改善点\n1. 動機が書かれていない\n   「後輩によって習熟度に差があり」\n   → なぜ自分が動いたのかが読めません\n   → （ここに、差を見て当時どう感じたかを書く）\n\n"
        "## 面接で聞かれそうなこと\n- なぜあなたが指導役を担ったのですか\n- 後輩から反発はありませんでしたか\n\n"
        "## 学生に確認すること\n**ESを補強するために聞くこと**\n- 差に気づいたきっかけは何でしたか\n- 結果として何が変わりましたか\n\n"
        "**自己分析として一緒に考えること**\n- 人に教えるとき大事にしていることは何ですか\n\n"
        "**面接に向けて準備を促すこと**\n- 「なぜその方法を選んだか」を1分で話せますか"
    )
