@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Сбор знаний из серверной resource. Lua не выполняются и не изменяются.
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\learn_mechanics.py
goto done
:use_python
python src\learn_mechanics.py
:done
echo.
pause
