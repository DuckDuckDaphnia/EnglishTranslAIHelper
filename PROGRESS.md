# 进度记录 (PROGRESS)

> 按时间倒序记录开发进展,方便回溯。

## 2026-09-08

- 需求梳理完成:网页应用 + Python 后端;两种翻译模式(中译英 / 英译中);AI 打分;GitHub 风格热力图打卡。
- 环境确认:Python 3.14.0、pip 26.1.1、uvicorn 0.52.1、httpx 已装;补装 fastapi 0.141.1。
- 确定文件类型:
  - 语料用 `.txt`(对程序 `readlines` 和大模型都最方便),每行一句;
  - 程序内部数据用 `.json`;
  - 任务/进度/错误记录用 `.md`。
- 确定技术方案:
  - 后端 FastAPI + httpx(不依赖具体厂商 SDK,支持所有 OpenAI 兼容接口与 Anthropic);
  - 前端原生 HTML/CSS/JS(无构建步骤);
  - 热力图采用 GitHub 绿色顺序渐变(单色相、亮度单调,亮/暗两套)。
- 完成全部代码:llm.py / storage.py / app.py / static(index.html、style.css、app.js)。
- 完成示例语料与初始数据、start.bat 启动脚本。
- 完成端到端自测:服务可启动,各接口连通,页面可访问(见 ERRORS.md 中的验证记录)。
- API Key 改为**优先读取环境变量 `ENGLISH_HELPER_API_KEY`**(更安全,密钥不落盘明文),`config.json` 的 `api_key` 仅作兜底;已验证优先级逻辑正确。

## 后续

- 待用户设置环境变量 `ENGLISH_HELPER_API_KEY` 后首次联调大模型。
- 根据实际使用反馈调整打分提示词与语料格式。
