# 📝 翻译练习助手 (EnglishTranslAIHelper)

一个网页版的中英翻译练习工具:给出原文,你来翻译,大模型批改并打分,配合 GitHub 风格的打卡热力图记录每天的练习量。

[English](./README.md) | 中文

## 功能

- **两种模式**
  - 🇨🇳 → 🇬🇧 中译英:给出中文,你翻译成英文,AI 批改英文译文。
  - 🇬🇧 → 🇨🇳 英译中:给出英文,你翻译成中文,AI 批改中文译文。
- **AI 批改**:每次提交后,大模型返回——标准译文、0-100 分、点评、亮点、改进建议。
- **打卡热力图**:按天统计翻译次数,渲染成 GitHub 风格的绿色热力图(近一年)。
- **历史记录**:保留最近 500 条翻译记录,可回看。
- **语料库选择**:网页可选择 `data/corpus/` 下任意文件夹作为语料库,按 U1→U2→… 自然序出题,支持上一题/下一题。
- **进度记忆**:上次所选语料库与做到第几题会记录在本地 `data/app/state.json`,重启后自动恢复。

## 文件类型约定

| 用途 | 类型 | 说明 |
|---|---|---|
| **语料** | `.txt` | 一个语料库 = `data/corpus/` 下一个含成对 `*En.txt`/`*Zh.txt` 文件的文件夹(每文件一段);UTF-8 或 GBK |
| 程序数据 | `.json` | `progress.json`(每日打卡)、`history.json`(翻译历史) |
| 文档/日志 | `.md` | TASKS / PROGRESS / ERRORS |

> 为什么语料用 `.txt`:对程序(`readlines`)和大模型 API 都是最方便、最通用的格式。

## 目录结构

```
EnglishTranslAIHelper/
├── app.py               # FastAPI 后端入口
├── llm.py               # 大模型 API 客户端
├── storage.py           # 数据存储(语料/进度/历史)
├── config.example.json  # 配置模板(复制为 config.json 自定义)
├── requirements.txt
├── start.bat            # Windows 一键启动脚本
├── README.md / README.zh-CN.md
├── TASKS.md / PROGRESS.md / ERRORS.md
├── static/              # 前端(index.html / style.css / app.js)
└── data/
    ├── corpus/
    │   ├── Xinshiye/one/    # 一个语料库文件夹:oneU1En.txt + oneU1Zh.txt、oneU2… …
    │   ├── en.example.txt   # 示例句子(见「添加你自己的语料」)
    │   └── zh.example.txt
    └── app/             # 运行时数据(state/progress/history,自动生成,已被 git 忽略)
```

## 安装

```bash
cd EnglishTranslAIHelper
python -m pip install -r requirements.txt
```

## 配置大模型 API

### 1. 设置 API Key(推荐:环境变量,不落盘明文)

把密钥放在环境变量 **`ENGLISH_HELPER_API_KEY`** 里:

```bat
:: Windows,永久生效
setx ENGLISH_HELPER_API_KEY "你的key"
```

设置后需**重新打开终端 / 重启服务**才生效。

也可以复制 `config.example.json` 为 `config.json` 并填入 key(仅作兜底,`config.json` 已被 git 忽略,不会上传)。

### 2. 配置模型与接口(config.json)

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

| 厂商 | provider | base_url | model 示例 |
|---|---|---|---|
| DeepSeek(默认) | openai_compatible | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | openai_compatible | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 通义千问 Qwen | openai_compatible | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Moonshot Kimi | openai_compatible | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 智谱 GLM | openai_compatible | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| Anthropic Claude | anthropic | `https://api.anthropic.com` | `claude-sonnet-5` |

> 只要厂商提供 OpenAI 兼容的 `/chat/completions` 接口,填对 `base_url` 和 `model` 即可,无需改代码。

## 启动

方式一(Windows 双击):

```
双击 start.bat
```

方式二(命令行):

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

然后浏览器打开 **http://127.0.0.1:8000**

## 使用

1. 选择模式(中译英 / 英译中)。
2. 在顶部下拉框选择一个语料库(`data/corpus/` 下每个文件夹是一个)。
3. 页面显示一段原文,在输入框写下你的翻译。
4. 点「提交,交给 AI 评分」(或 Ctrl+Enter)。
5. 查看分数、标准译文、点评、亮点与改进建议。
6. 点「上一题 / 下一题」按顺序切换;热力图和统计会自动更新。

## 添加你自己的语料

语料目录已被 **git 忽略**(你的个人句子不会被提交)。

把每个语料库单独放进 `data/corpus/` 下的一个文件夹。文件夹内放成对文件——同一前缀、一个英文(`*En.txt`)+ 一个中文(`*Zh.txt`)为一题:

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

每对文件即一题,按自然序(U1 → U2 → … → U10)出题。网页会把每个文件夹列为一个可选语料库,并在 `data/app/state.json` 记住你上次的选择与题号。

## 安全说明

- API Key 优先读取环境变量 `ENGLISH_HELPER_API_KEY`(回退到 `config.json`)。
- `config.json`、`.env`、`data/app/`(翻译历史 / 进度 / 错误日志)、以及 `data/corpus/*`(你的个人语料)均已被 **git 忽略**,不会被提交到仓库。

## 常见问题

- **提示「尚未配置 API Key」**:设置环境变量 `ENGLISH_HELPER_API_KEY`(或在 `config.json` 里填 key)后重启服务。
- **设置了环境变量但不生效**:`setx` 只对新开的终端生效,请关闭当前终端/服务后重开;或直接在 `config.json` 里临时填 key 兜底。
- **提示「API Key 无效」**:检查 key 是否填对、是否有余额、`base_url` 是否匹配厂商。
- **提示「语料为空」**:`data/corpus/` 下还没有含成对 `*En.txt`/`*Zh.txt` 文件的语料库文件夹。
- **打分/点评不符合预期**:可在 `llm.py` 的提示词里调整评分维度与要求。
- **大模型调用报错详情**:查看 `data/app/errors.log`。
