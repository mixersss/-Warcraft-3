@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python src\validate_dialogue.py
) else (
  py -3 src\validate_dialogue.py
)
pause
