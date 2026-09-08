@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动翻译练习助手...
echo 启动成功后,请用浏览器打开: http://127.0.0.1:8000
echo 按 Ctrl+C 可以停止服务
echo.
if "%ENGLISH_HELPER_API_KEY%"=="" (
  echo [提示] 未检测到环境变量 ENGLISH_HELPER_API_KEY,可在 config.json 里填 api_key 兜底。
  echo.
)
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
