@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo Режим разработчика: нужен локальный Python 3.11+.
echo Для работодателя используйте ЗАПУСТИТЬ_ДЕМО.bat

set "ROOT=%~dp0.."
set "PYTHONPATH=%ROOT%\backend"
set "LEADASSIGN_STATIC_DIR=%ROOT%\backend\static"

where python >nul 2>&1
if errorlevel 1 (
  echo Python не найден в PATH.
  pause
  exit /b 1
)

python "%ROOT%\backend\run_portable.py"
pause
endlocal
