@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python src\restore_shop_knowledge.py
) else (
  py -3 src\restore_shop_knowledge.py
)
pause
