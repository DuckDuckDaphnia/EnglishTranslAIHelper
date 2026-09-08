# 错误日志 (ERRORS)

> 记录开发与联调过程中遇到的问题及解决方式,方便回溯。
> 另外,程序运行时的大模型接口错误会自动追加到 `data/app/errors.log`。

## 规则

- 每个条目记录:日期、现象、原因、解决方式。
- 已解决的标 ✅,待解决的标 ⏳。

## 记录

### 2026-09-08

- ✅ **现象**:环境里 `python3` 命令不可用(Windows 上只有 `python`)。
  - **原因**:Windows 官方 Python 安装默认不带 `python3` 别名,且系统有「应用执行别名」干扰。
  - **解决**:统一使用 `python` 命令;启动脚本 `start.bat` 中也用 `python`。

- ✅ **现象**:环境中缺 `fastapi` 模块。
  - **原因**:初始环境未安装。
  - **解决**:`python -m pip install fastapi`,成功安装 fastapi 0.141.1(pydantic 2.13.4 已存在)。

- ✅ **现象**:`.txt` 语料在不同电脑上可能因编码(UTF-8 / GBK / 带 BOM)读取报错。
  - **原因**:中文 Windows 常用记事本默认可能是 GBK,或文件带 UTF-8 BOM。
  - **解决**:`storage._read_text_file` 按 `utf-8-sig → utf-8 → gbk` 顺序尝试解码,失败时用 `ignore` 兜底。

- ✅ **现象**:大模型返回的 JSON 可能被包在 markdown 代码块或前后夹杂文字。
  - **原因**:不同模型对「只返回 JSON」指令的遵守程度不同。
  - **解决**:`llm.parse_llm_json` 做了三级兜底(直接解析 → 去代码块 → 截取首尾花括号)。

- ✅ **现象**:测试时 `storage.get_corpus_stats()` 返回 0,语料读取不到。
  - **原因**:示例语料写在 `data/corpus/en.txt`、`data/corpus/zh.txt`,而 `load_corpus` 只扫描 `data/corpus/en/`、`data/corpus/zh/` 子目录,位置不匹配。
  - **解决**:`load_corpus` 改为同时支持「单文件 `data/corpus/{lang}.txt`」和「目录 `data/corpus/{lang}/*.txt`」两种放置方式,已验证读取 12+12 句正常。

- ⏳ **待验证**:真实 API Key 联调时,不同厂商对 `max_tokens`、`temperature` 的支持差异。
  - **备注**:若某厂商报「不支持的参数」,可在 `llm.py` 中按需裁剪请求字段。

（暂无其他记录,保持更新）
