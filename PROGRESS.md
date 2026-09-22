# 进度记录 (PROGRESS)

> 按时间倒序记录开发进展,方便回溯。

## 2026-09-22

- 新增「语料库选择」:网页顶部下拉框可选择 `data/corpus/` 下不同文件夹内的语料(如 `Xinshiye/one`)。
- 新增「顺序出题」:所选语料库按 U1→U2→…→U8 自然序出题,支持上一题 / 下一题。
- 新增「进度记忆」:本地 `data/app/state.json` 记录上次所选语料库与题号,刷新后自动恢复。
- 后端:`storage.py` 新增 `list_corpora`/`load_corpus_items`/`get_sentence`/`load_state`/`save_state` 与自然排序 `_pair_files`;`app.py` 新增 `/api/corpora`、`/api/state`,`/api/sentence` 支持 `corpus`/`index` 参数;前端 `index.html`/`app.js`/`style.css` 相应改造。
- 同步更新中英 README(`README.md`/`README.zh-CN.md`),补充「语料库选择 / 顺序出题 / 进度记忆」说明与语料目录结构示例。

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

- 完成 git 上传前的**安全审查**:全项目扫描无任何密钥(api_key 在环境变量);新增 `.gitignore`(忽略 `config.json`、`data/app/`、`.env`)、`config.example.json` 模板;`app.py` 增加 config.json 缺失时回退到 example 的能力。
- 完成中英双 README(`README.md` 英文 + `README.zh-CN.md` 中文,互相链接)。
- 完成本地 git 提交(17 个文件,含 `config.example.json`,不含任何敏感信息)。
- ✅ 推送 GitHub 成功(用户开启 VPN 后):`git push -u origin main --force` 覆盖了远程占位 README,远程 17 个文件已就绪;已复核确认无敏感文件泄漏。
- ✅ 按用户要求将语料加入 git 忽略(`data/corpus/*`,仅保留 `*.example.txt` 示例),个人句子不再提交;两份 README 已同步说明。

## 后续

- 待用户设置环境变量 `ENGLISH_HELPER_API_KEY` 后首次联调大模型。
- 根据实际使用反馈调整打分提示词与语料格式。
