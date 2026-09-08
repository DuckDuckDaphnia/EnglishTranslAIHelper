"""llm.py — 大模型 API 客户端

支持两种接口:
1. openai_compatible — 兼容 OpenAI 的 /chat/completions 接口
   (DeepSeek / OpenAI / 通义千问 / Kimi / GLM / Moonshot 等)
2. anthropic — Anthropic Messages API (Claude)

统一返回评测结果 dict:
    {
        "score": int,           # 0-100 综合分
        "corrected": str,       # 修改后的标准译文
        "feedback": str,        # 中文点评
        "highlights": [str],    # 亮点
        "improvements": [str],  # 改进建议
    }
"""
import json
import re

import httpx

SYSTEM_PROMPT = (
    "你是一位专业的翻译老师,擅长中英互译教学。"
    "你负责批改学生的翻译作业,给出修改后的标准译文、打分和点评。"
)

# 示例 JSON,单独定义避免 f-string 花括号转义问题
_EXAMPLE = (
    '{"score": 85, "corrected": "标准译文", "feedback": "点评内容", '
    '"highlights": ["亮点1"], "improvements": ["改进点1"]}'
)


def build_user_prompt(mode, source, user_translation):
    """根据模式生成批改提示词。"""
    if mode == "zh2en":
        direction = "中文 → 英文:原文是中文,学生把它翻译成了英文,请批改英文译文。"
    else:
        direction = "英文 → 中文:原文是英文,学生把它翻译成了中文,请批改中文译文。"
    return (
        "请批改下面的翻译练习。\n\n"
        f"【翻译方向】{direction}\n"
        f"【原文】{source}\n"
        f"【学生的翻译】{user_translation}\n\n"
        "请完成以下任务:\n"
        "1. 给出修改后的标准译文(字段 corrected)\n"
        "2. 从“准确性、流畅度、用词地道程度”三个维度综合打分,0-100 的整数(字段 score)\n"
        "3. 用中文给出简明的点评和修改建议,2-4 句(字段 feedback)\n"
        "4. 指出学生翻译中的亮点,最多 3 条(字段 highlights,字符串数组)\n"
        "5. 指出需要改进的地方,最多 3 条(字段 improvements,字符串数组)\n\n"
        "只返回一个 JSON 对象,不要输出任何其他文字或代码块标记。格式如下:\n"
        + _EXAMPLE
    )


def parse_llm_json(text):
    """从大模型返回的文本中稳健地解析出 JSON 对象。"""
    if not text:
        raise ValueError("大模型返回内容为空")
    text = text.strip()
    # 1) 直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) 去掉 markdown 代码块标记
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            pass
    # 3) 截取第一个 { 到最后一个 } 之间的内容
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    raise ValueError("无法从大模型返回中解析出 JSON: " + text[:200])


def _as_str_list(value):
    """把任意返回值规范化为字符串列表。"""
    if value is None:
        return []
    if isinstance(value, str):
        lines = [x.strip() for x in value.splitlines() if x.strip()]
        return lines if lines else ([value.strip()] if value.strip() else [])
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value)] if str(value).strip() else []


async def _call_openai_compatible(config, messages):
    base = config["base_url"].rstrip("/")
    url = base if base.endswith("/chat/completions") else base + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": config.get("temperature", 0.3),
        "max_tokens": 2048,
    }
    timeout = config.get("timeout_seconds", 60)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("接口返回格式异常: " + json.dumps(data, ensure_ascii=False)[:300])


async def _call_anthropic(config, messages):
    base = config["base_url"].rstrip("/")
    url = base if base.endswith("/messages") else base + "/v1/messages"
    headers = {
        "x-api-key": config["api_key"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    system = None
    user_content = ""
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        elif m["role"] == "user":
            user_content = m["content"]
    payload = {
        "model": config["model"],
        "max_tokens": 2048,
        "temperature": config.get("temperature", 0.3),
        "messages": [{"role": "user", "content": user_content}],
    }
    if system:
        payload["system"] = system
    timeout = config.get("timeout_seconds", 60)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    try:
        return data["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("接口返回格式异常: " + json.dumps(data, ensure_ascii=False)[:300])


async def evaluate(mode, source, user_translation, config):
    """调用大模型批改翻译,返回统一结构的评测结果。"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(mode, source, user_translation)},
    ]
    provider = config.get("provider", "openai_compatible")
    if provider == "anthropic":
        raw = await _call_anthropic(config, messages)
    else:
        raw = await _call_openai_compatible(config, messages)

    data = parse_llm_json(raw)
    try:
        score = int(round(float(data.get("score", 0))))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))

    return {
        "score": score,
        "corrected": str(data.get("corrected", "")).strip(),
        "feedback": str(data.get("feedback", "")).strip(),
        "highlights": _as_str_list(data.get("highlights")),
        "improvements": _as_str_list(data.get("improvements")),
    }
