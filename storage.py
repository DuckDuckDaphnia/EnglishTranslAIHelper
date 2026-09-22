"""storage.py — 数据存储层

负责:
- 读取语料(data/corpus/en 与 data/corpus/zh 下的 .txt 文件,每行一句)
- 持久化每日进度(progress.json)与翻译历史(history.json)
- 生成热力图数据与统计信息

文件约定:
- 语料文件类型:.txt(UTF-8 或 GBK 均可),每行一句,空行和 # 开头的行会被忽略
- 进度/历史:.json
"""
import json
import random
import re
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CORPUS_ROOT = BASE_DIR / "data" / "corpus"
CORPUS_EN_DIR = CORPUS_ROOT / "en"
CORPUS_ZH_DIR = CORPUS_ROOT / "zh"
APP_DATA_DIR = BASE_DIR / "data" / "app"
PROGRESS_FILE = APP_DATA_DIR / "progress.json"
HISTORY_FILE = APP_DATA_DIR / "history.json"
ERROR_LOG_FILE = APP_DATA_DIR / "errors.log"
STATE_FILE = APP_DATA_DIR / "state.json"

# 历史最多保留条数,避免文件无限增长
HISTORY_LIMIT = 500


def _ensure_dirs():
    for d in (CORPUS_EN_DIR, CORPUS_ZH_DIR, APP_DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not PROGRESS_FILE.exists():
        PROGRESS_FILE.write_text("{}", encoding="utf-8")
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")


_ensure_dirs()


def _read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_text_file(path):
    """按 UTF-8(带 BOM)/GBK 顺序尝试解码,兼容中文 Windows 常见编码。"""
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _corpus_files(lang):
    """收集某语言的全部语料文件,按绝对路径去重。

    支持三种放置方式(可同时使用):
    1. 目录:data/corpus/{lang}/ 下的所有 .txt 文件
    2. 单文件:data/corpus/{lang}.txt
    3. 递归:data/corpus/ 下文件名以 En.txt / Zh.txt 结尾的文件
       (例如 data/corpus/Xinshiye/one/oneU1En.txt)
    """
    d = CORPUS_EN_DIR if lang == "en" else CORPUS_ZH_DIR
    suffix = "en.txt" if lang == "en" else "zh.txt"

    files = []
    seen = set()
    for f in sorted(d.glob("*.txt")):
        seen.add(f)
        files.append(f)
    single = BASE_DIR / "data" / "corpus" / f"{lang}.txt"
    if single.exists() and single not in seen:
        seen.add(single)
        files.append(single)
    corpus_root = BASE_DIR / "data" / "corpus"
    for f in sorted(corpus_root.rglob("*.txt")):
        if f.name.lower().endswith(suffix) and f not in seen:
            seen.add(f)
            files.append(f)
    return files


def load_corpus(lang):
    """读取指定语言语料,lang = 'en' 或 'zh'。返回非空句子(或段落)列表。

    每行作为一个独立条目;空行和 # 开头的行会被忽略。
    """
    sentences = []
    for f in _corpus_files(lang):
        text = _read_text_file(f)
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                sentences.append(s)
    return sentences


def get_random_sentence(lang):
    """随机取一句语料,为空时返回 None。"""
    sentences = load_corpus(lang)
    if not sentences:
        return None
    return random.choice(sentences)


def get_corpus_stats():
    return {"en": len(load_corpus("en")), "zh": len(load_corpus("zh"))}


# ---------- 语料库(文件夹)选择与顺序出题 ----------

def _natural_key(s):
    """自然排序键:把数字段转成 int,使 U1 < U2 < ... < U10。"""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", s)]


def _pair_files(d):
    """在目录 d 下,按「去掉末尾 En.txt / Zh.txt 得到的 base」把中英文配对。

    返回 [(base, en_path, zh_path)],base 保留原大小写,按自然序排序。
    """
    en = {}
    zh = {}
    for f in d.glob("*.txt"):
        name = f.name
        low = name.lower()
        if low.endswith("en.txt"):
            en[low[:-6]] = (name[:-6], f)
        elif low.endswith("zh.txt"):
            zh[low[:-6]] = f
    bases = sorted(set(en) & set(zh), key=_natural_key)
    return [(en[b][0], en[b][1], zh[b]) for b in bases]


def list_corpora():
    """列出 data/corpus/ 下可作为语料库的文件夹(直接包含 *En.txt/*Zh.txt 对)。"""
    corpora = []
    for d in sorted(CORPUS_ROOT.rglob("*")):
        if not d.is_dir():
            continue
        pairs = _pair_files(d)
        if pairs:
            rel = d.relative_to(CORPUS_ROOT).as_posix()
            corpora.append({"id": rel, "name": rel, "count": len(pairs)})
    return corpora


def load_corpus_items(corpus_id):
    """返回某语料库的有序题目列表 [{key, en, zh}],每对文件整段即一题。"""
    items = []
    for base, en_path, zh_path in _pair_files(CORPUS_ROOT / corpus_id):
        en = _read_text_file(en_path).strip()
        zh = _read_text_file(zh_path).strip()
        if en or zh:
            items.append({"key": base, "en": en, "zh": zh})
    return items


def get_sentence(corpus_id, mode, index=0):
    """取某语料库第 index 题;zh2en 返回中文,en2zh 返回英文;越界循环。"""
    items = load_corpus_items(corpus_id)
    if not items:
        return None
    item = items[int(index) % len(items)]
    return item["zh"] if mode == "zh2en" else item["en"]


def load_state():
    """读取上次的语料库与题号,无记录时返回默认。"""
    return _read_json(STATE_FILE, {"corpus": None, "index": 0})


def save_state(corpus, index):
    """保存当前语料库与题号。"""
    _write_json(STATE_FILE, {"corpus": corpus, "index": int(index)})


def record_translation(mode, source, user_translation, result):
    """记录一次翻译:更新每日进度 + 追加历史。"""
    now = datetime.now()
    date_key = now.strftime("%Y-%m-%d")

    progress = _read_json(PROGRESS_FILE, {})
    day = progress.get(date_key, {"count": 0, "total_score": 0})
    day["count"] = day.get("count", 0) + 1
    day["total_score"] = day.get("total_score", 0) + result["score"]
    day["avg_score"] = round(day["total_score"] / day["count"], 1)
    progress[date_key] = day
    _write_json(PROGRESS_FILE, progress)

    history = _read_json(HISTORY_FILE, [])
    history.append(
        {
            "id": now.strftime("%Y%m%d%H%M%S%f"),
            "timestamp": now.isoformat(timespec="seconds"),
            "date": date_key,
            "mode": mode,
            "source": source,
            "user_translation": user_translation,
            "corrected": result["corrected"],
            "score": result["score"],
            "feedback": result["feedback"],
            "highlights": result["highlights"],
            "improvements": result["improvements"],
        }
    )
    _write_json(HISTORY_FILE, history[-HISTORY_LIMIT:])


def get_heatmap(days=371):
    """返回近 days 天的 {date_str: {count, avg_score}},覆盖每一天。"""
    progress = _read_json(PROGRESS_FILE, {})
    today = date.today()
    result = {}
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        key = d.isoformat()
        day = progress.get(key)
        if day:
            count = day.get("count", 0)
            total = day.get("total_score", 0)
            result[key] = {
                "count": count,
                "avg_score": round(total / count, 1) if count else 0,
            }
        else:
            result[key] = {"count": 0, "avg_score": 0}
    return result


def get_stats():
    """返回今日次数、总次数、历史平均分。"""
    progress = _read_json(PROGRESS_FILE, {})
    today = date.today().isoformat()
    today_count = progress.get(today, {}).get("count", 0)
    total_count = sum(d.get("count", 0) for d in progress.values())
    total_score = sum(d.get("total_score", 0) for d in progress.values())
    avg = round(total_score / total_count, 1) if total_count else 0
    return {"today_count": today_count, "total_count": total_count, "avg_score": avg}


def get_history(limit=20):
    """返回最近 limit 条历史,最新的在前。"""
    history = _read_json(HISTORY_FILE, [])
    return history[-limit:][::-1]


def log_error(message):
    """把运行时错误追加到 errors.log(用于排查 API 等问题)。"""
    ts = datetime.now().isoformat(timespec="seconds")
    try:
        with ERROR_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass
