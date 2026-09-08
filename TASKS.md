# 任务清单 (TASKS)

> 本文件记录项目的任务分解与完成状态。状态:`[x]` 已完成,`[ ]` 待办。

## 开发任务

- [x] 搭建项目结构与跟踪文件(config.json / requirements.txt / TASKS / PROGRESS / ERRORS / README)
- [x] 实现 LLM 客户端 `llm.py`(OpenAI 兼容接口 + Anthropic 接口,统一返回评测结果)
- [x] 实现数据存储 `storage.py`(语料读取、进度/历史持久化、热力图、统计)
- [x] 实现后端 `app.py`(FastAPI 路由:config / sentence / evaluate / heatmap / stats / history)
- [x] 实现前端页面(双模式切换、翻译输入、AI 评分结果、GitHub 风格热力图、历史记录)
- [x] 创建示例语料与初始数据(data/corpus/en.txt、zh.txt、progress.json、history.json)
- [x] 端到端测试(服务启动、接口连通、页面可访问)
- [x] API Key 改为优先读取环境变量 `ENGLISH_HELPER_API_KEY`(config.json 仅作兜底)
- [ ] 用户设置环境变量后首次联调(需用户提供 key)

## 待用户确认 / 后续可扩展(非必需)

- [ ] 选择默认大模型供应商(当前默认 DeepSeek,可在 config.json 切换)
- [ ] 语料去重 / 顺序模式(当前为随机取句)
- [ ] 自定义打分权重与提示词
- [ ] 导出历史记录 / 统计报表

## 文件类型约定(已确定)

- **语料(用户文本)**:`.txt`,UTF-8 或 GBK 编码均可,每行一句,空行和 `#` 开头行忽略。
  - 英文原文放 `data/corpus/en/`,中文原文放 `data/corpus/zh/`。
- **程序数据**:`.json`(progress.json 记录每日打卡,history.json 记录翻译历史)。
- **任务/进度/错误记录**:`.md`(本文件 + PROGRESS.md + ERRORS.md)。
