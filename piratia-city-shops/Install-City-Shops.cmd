@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Останови ботов и GameServer, закрой клиент Game.exe.
echo Пять координат уже настроены. Нужны папки сервера и клиента.
echo Сервер: GameServer или resource. Клиент: отдельная папка игры с Game.exe.
echo Будут синхронизированы цены выбранных предметов на сервере и в клиенте.
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 native\installer.py --apply
goto done
:use_python
python native\installer.py --apply
:done
echo.
pause
