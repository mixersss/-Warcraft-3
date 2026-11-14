@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set "PIRATIA_NPC_QUERY="
set /p "PIRATIA_NPC_QUERY=Имя НПС, услуга (банк), товар (кольца) или ID вещи; Enter — все: "
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\show_npcs.py --query-env PIRATIA_NPC_QUERY
goto done
:use_python
python src\show_npcs.py --query-env PIRATIA_NPC_QUERY
:done
echo.
pause
