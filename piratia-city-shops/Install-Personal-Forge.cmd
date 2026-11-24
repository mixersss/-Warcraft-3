@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Перед установкой останови GameServer.
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 personal_forge.py --apply
goto done
:use_python
python personal_forge.py --apply
:done
pause
