@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Останови GameServer и закрой игровой клиент.
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 world_expansion.py --apply
goto done
:use_python
python world_expansion.py --apply
:done
pause
