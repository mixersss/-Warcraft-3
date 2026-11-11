@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if not errorlevel 1 goto use_py
python -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if not errorlevel 1 goto use_python
echo Python 3.9+ is required. Use the Python installed for your bots.
goto done
:use_py
py -3 convert_music.py %*
goto done
:use_python
python convert_music.py %*
:done
echo.
pause
