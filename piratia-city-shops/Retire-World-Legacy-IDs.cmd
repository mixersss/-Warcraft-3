@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Продолжай только после переноса или расходования старых предметов у всех персонажей, включая их склады.
echo Установщик создаст резервную копию таблиц. Инвентари персонажей он не проверяет.
choice /C YN /M "Старых гемов и трофеев больше нет, удалить прежние ID из таблиц"
if errorlevel 2 exit /b 0
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 world_expansion.py --apply --retire-legacy-ids
goto done
:use_python
python world_expansion.py --apply --retire-legacy-ids
:done
pause
