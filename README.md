# 📝 EnglishTranslAIHelper

A web-based Chinese–English translation practice tool. You translate, an LLM grades and corrects you, and a GitHub-style streak heatmap tracks your daily practice.

[中文文档](./README.zh-CN.md) | English

## Features

- **Two modes**
  - 🇨🇳 → 🇬🇧 Chinese→English: given Chinese, you translate into English, AI corrects the English.
  - 🇬🇧 → 🇨🇳 English→Chinese: given English, you translate into Chinese, AI corrects the Chinese.
- **AI grading**: each submission returns a corrected translation, a 0–100 score, feedback, highlights, and suggestions.
- **Streak heatmap**: daily translation counts rendered as a GitHub-style green heatmap (past year).
- **History**: keeps the last 500 translations for review.
- **Corpus selection**: pick any folder under `data/corpus/` as your corpus; questions are served in natural order (U1 → U2 → …) with Previous/Next buttons.
- **Resume**: your last corpus and position are remembered locally (`data/app/state.json`) across restarts.

## File type conventions

| Purpose | Type | Notes |
|---|---|---|
| **Corpus** | `.txt` | A corpus is a folder under `data/corpus/` with paired `*En.txt` / `*Zh.txt` files (one paragraph per file); UTF-8 or GBK |
| App data | `.json` | `progress.json` (daily stats), `history.json` (history) |
| Docs / logs | `.md` | TASKS / PROGRESS / ERRORS |

> Why `.txt` for the corpus: it's the simplest format for both program parsing (`readlines`) and LLM APIs.

## Project structure

```
EnglishTranslAIHelper/
├── app.py               # FastAPI backend
├── llm.py               # LLM API client
├── storage.py           # Data layer (corpus / progress / history)
├── config.example.json  # Config template (copy to config.json to customize)
├── requirements.txt
├── start.bat            # Windows one-click launcher
├── README.md / README.zh-CN.md
├── TASKS.md / PROGRESS.md / ERRORS.md
├── static/              # Frontend (index.html / style.css / app.js)
└── data/
    ├── corpus/
    │   ├── Xinshiye/one/    # a corpus folder: oneU1En.txt + oneU1Zh.txt, oneU2..., ...
    │   ├── en.example.txt   # example sentences (see "Adding your own corpus")
    │   └── zh.example.txt
    └── app/             # Auto-generated runtime data (state/progress/history, git-ignored)
```

## Installation

```bash
cd EnglishTranslAIHelper
python -m pip install -r requirements.txt
```

## Configuration

### 1. Set your API key (recommended: environment variable)

Store the key in the **`ENGLISH_HELPER_API_KEY`** environment variable so it never lives in a file:

```bat
:: Windows, permanent
setx ENGLISH_HELPER_API_KEY "your-key"
```

Restart your terminal / the app afterwards.

Alternatively, copy `config.example.json` to `config.json` and put the key there (only as a fallback; `config.json` is git-ignored).

### 2. Choose the model / provider (config.json)

```json
{
  "provider": "openai_compatible",
  "base_url": "https://api.deepseek.com/v1",
  "api_key": "",
  "model": "deepseek-chat",
  "temperature": 0.3,
  "timeout_seconds": 60
}
```

| Provider | provider | base_url | model example |
|---|---|---|---|
| DeepSeek (default) | openai_compatible | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | openai_compatible | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Qwen | openai_compatible | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Moonshot Kimi | openai_compatible | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Zhipu GLM | openai_compatible | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| Anthropic Claude | anthropic | `https://api.anthropic.com` | `claude-sonnet-5` |

> Any provider exposing an OpenAI-compatible `/chat/completions` endpoint works — just set `base_url` and `model`. No code changes needed.

## Run

Windows (double-click `start.bat`), or:

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Then open **http://127.0.0.1:8000**.

## Usage

1. Pick a mode (Chinese→English / English→Chinese).
2. Pick a corpus from the top dropdown (each folder under `data/corpus/` is one).
3. A source passage is shown — type your translation.
4. Click **Submit** (or Ctrl+Enter).
5. Review the score, corrected translation, feedback, highlights and suggestions.
6. Use **Previous / Next** to move through questions in order; the heatmap and stats update automatically.

## Adding your own corpus

The corpus is **git-ignored** (your personal sentences are never committed).

Organize each corpus as a folder under `data/corpus/`. Inside a folder, put paired files sharing a common prefix — one English (`*En.txt`) and one Chinese (`*Zh.txt`) per unit:

```
data/corpus/
├── Xinshiye/
│   └── one/
│       ├── oneU1En.txt   +   oneU1Zh.txt
│       ├── oneU2En.txt   +   oneU2Zh.txt
│       └── ...
└── MyBook/
    ├── U1En.txt   +   U1Zh.txt
    └── ...
```

Each pair is one question; they are served in natural order (U1 → U2 → … → U10). The web UI lists every folder as a selectable corpus, and remembers your last choice and position in `data/app/state.json`.

## Security

- The API key is read from the `ENGLISH_HELPER_API_KEY` environment variable (falls back to `config.json`).
- `config.json`, `.env`, `data/app/` (translation history / progress / error logs), and `data/corpus/*` (your personal sentences) are **git-ignored** and never committed.

## FAQ

- **"尚未配置 API Key" / "API key not configured"**: set `ENGLISH_HELPER_API_KEY` (or fill `config.json`) and restart.
- **"API Key 无效" / "invalid API key"**: check the key, your balance, and that `base_url` matches the provider.
- **"语料为空" / "corpus empty"**: no corpus folder (with paired `*En.txt`/`*Zh.txt` files) under `data/corpus/`.
- **Scoring / feedback not to your liking**: adjust the prompt in `llm.py`.
- **LLM call errors**: see `data/app/errors.log` (auto-created on error).
