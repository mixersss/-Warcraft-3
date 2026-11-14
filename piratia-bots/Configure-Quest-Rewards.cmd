@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Настройка наград: опыт за квесты x9, золото за квесты x5.
echo Утилита сохранит резервную копию Lua-файла. Понадобится перезапуск GameServer.
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 src\configure_quest_rewards.py --exp 9 --gold 5
goto done
:use_python
python src\configure_quest_rewards.py --exp 9 --gold 5
:done
echo.
pause
