@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python src\configure_chat.py
) else (
  py -3 src\configure_chat.py
)
pause
