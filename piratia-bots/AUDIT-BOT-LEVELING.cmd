@echo off
cd /d "%~dp0"
python src\audit_leveling.py "%~dp0."
pause
