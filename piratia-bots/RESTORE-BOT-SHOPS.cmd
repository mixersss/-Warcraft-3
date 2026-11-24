@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python src\restore_shop_knowledge.py %*
) else (
  py -3 src\restore_shop_knowledge.py %*
)
set "result=%errorlevel%"
pause
exit /b %result%
