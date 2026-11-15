@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Закрой клиент Game.exe. Серверные файлы эта команда не меняет.
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 native\installer.py --client-only --apply
goto done
:use_python
python native\installer.py --client-only --apply
:done
pause
