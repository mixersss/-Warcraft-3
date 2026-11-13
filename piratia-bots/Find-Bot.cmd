@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set "PIRATIA_BOT_NAME="
set /p "PIRATIA_BOT_NAME=Ник бота (например Bot38977e75): "
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\show_diagnostics.py --name-env PIRATIA_BOT_NAME
goto done
:use_python
python src\show_diagnostics.py --name-env PIRATIA_BOT_NAME
:done
echo.
pause
