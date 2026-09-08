"""app.py — 翻译练习助手后端(FastAPI)

启动方式:
    python -m uvicorn app:app --host 127.0.0.1 --port 8000
然后浏览器打开 http://127.0.0.1:8000
"""
import json
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import llm
import storage

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
STATIC_DIR = BASE_DIR / "static"

# API Key 的环境变量名:优先读取环境变量,config.json 仅作兜底
ENV_API_KEY = "ENGLISH_HELPER_API_KEY"

app = FastAPI(title="翻译练习助手")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class EvaluateRequest(BaseModel):
    mode: str  # "zh2en" 或 "en2zh"
    source: str
    user_translation: str


def load_config():
    # 优先 config.json;不存在时回退到 config.example.json(便于新克隆者直接运行)
    path = CONFIG_FILE if CONFIG_FILE.exists() else BASE_DIR / "config.example.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    # 环境变量优先:如果设置了 ENGLISH_HELPER_API_KEY,则覆盖文件中的 api_key
    env_key = os.environ.get(ENV_API_KEY, "").strip()
    if env_key:
        cfg["api_key"] = env_key
    return cfg


def _has_key(cfg):
    key = (cfg.get("api_key") or "").strip()
    return bool(key) and key not in ("请在这里填写你的API Key", "sk-xxx")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/config")
def api_config():
    cfg = load_config()
    return {
        "provider": cfg.get("provider"),
        "model": cfg.get("model"),
        "has_key": _has_key(cfg),
        "corpus": storage.get_corpus_stats(),
    }


@app.get("/api/sentence")
def api_sentence(mode: str = "zh2en"):
    if mode not in ("zh2en", "en2zh"):
        raise HTTPException(status_code=400, detail="mode 必须是 zh2en 或 en2zh")
    lang = "zh" if mode == "zh2en" else "en"
    sentence = storage.get_random_sentence(lang)
    if sentence is None:
        raise HTTPException(
            status_code=404,
            detail=f"语料为空,请往 data/corpus/{lang} 目录添加 .txt 文本(每行一句)",
        )
    return {"mode": mode, "source": sentence}


@app.post("/api/evaluate")
async def api_evaluate(req: EvaluateRequest):
    if req.mode not in ("zh2en", "en2zh"):
        raise HTTPException(status_code=400, detail="mode 必须是 zh2en 或 en2zh")
    if not req.source.strip() or not req.user_translation.strip():
        raise HTTPException(status_code=400, detail="原文和翻译都不能为空")

    cfg = load_config()
    if not _has_key(cfg):
        raise HTTPException(
            status_code=400,
            detail="尚未配置 API Key,请在 config.json 中填写 api_key 后重启服务",
        )

    try:
        result = await llm.evaluate(req.mode, req.source, req.user_translation, cfg)
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status in (401, 403):
            detail = "API Key 无效或无权限,请检查 config.json 中的 api_key"
        elif status == 429:
            detail = "请求过于频繁或额度不足 (HTTP 429)"
        else:
            detail = f"大模型接口返回错误 (HTTP {status})"
        storage.log_error(detail)
        raise HTTPException(status_code=502, detail=detail)
    except httpx.HTTPError as e:
        detail = f"无法连接大模型接口:{e}"
        storage.log_error(detail)
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:  # noqa: BLE001
        detail = f"大模型调用失败:{e}"
        storage.log_error(detail)
        raise HTTPException(status_code=502, detail=detail)

    storage.record_translation(req.mode, req.source, req.user_translation, result)
    return {"result": result, "stats": storage.get_stats()}


@app.get("/api/heatmap")
def api_heatmap():
    return {"data": storage.get_heatmap()}


@app.get("/api/stats")
def api_stats():
    return storage.get_stats()


@app.get("/api/history")
def api_history(limit: int = 20):
    return {"history": storage.get_history(limit)}
