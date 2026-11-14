@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
echo Сначала останови сервер. Боты и data этим установщиком не изменяются.
echo Пять мест в центре Аргента уже выбраны; координаты вводить не нужно.
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 install.py --apply
goto done
:use_python
python install.py --apply
:done
echo.
pause
