@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set "PIRATIA_MECHANIC_QUERY="
set /p "PIRATIA_MECHANIC_QUERY=Механика (форж, корабли, феи, ДВ, топи) или ID предмета; Enter — все: "
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\show_mechanics.py --query-env PIRATIA_MECHANIC_QUERY
goto done
:use_python
python src\show_mechanics.py --query-env PIRATIA_MECHANIC_QUERY
:done
echo.
pause
