@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo Остановка LeadAssign Demo...

if not exist "runtime\app.pid" (
  echo Приложение уже остановлено.
  pause
  exit /b 0
)

set /p PID=<"runtime\app.pid"
if not defined PID (
  echo Приложение уже остановлено.
  del /f /q "runtime\app.pid" >nul 2>&1
  pause
  exit /b 0
)

tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
if errorlevel 1 (
  echo Приложение уже остановлено.
  del /f /q "runtime\app.pid" >nul 2>&1
  if exist "runtime\port.txt" del /f /q "runtime\port.txt" >nul 2>&1
  pause
  exit /b 0
)

taskkill /PID %PID% /T /F >nul 2>&1
if errorlevel 1 (
  echo Не удалось остановить процесс PID %PID%.
  pause
  exit /b 1
)

del /f /q "runtime\app.pid" >nul 2>&1
if exist "runtime\port.txt" del /f /q "runtime\port.txt" >nul 2>&1
echo Приложение остановлено.
pause
endlocal
