@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\configure_dungeon_maps.py --apply
goto done
:use_python
python src\configure_dungeon_maps.py --apply
:done
echo.
pause
