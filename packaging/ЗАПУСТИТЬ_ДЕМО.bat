@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================
echo  LeadAssign Demo — Немецкие ОКНА Бел
echo  Демонстрационный прототип (синтетические данные)
echo ============================================
echo.

if not exist "app\GermanWindowsAI.exe" (
  echo [ОШИБКА] Не найден app\GermanWindowsAI.exe
  echo Убедитесь, что архив распакован полностью.
  pause
  exit /b 1
)

if not exist "runtime" mkdir "runtime"
if not exist "runtime\logs" mkdir "runtime\logs"

if exist "runtime\app.pid" (
  set /p OLD_PID=<"runtime\app.pid"
  if defined OLD_PID (
    tasklist /FI "PID eq %OLD_PID%" 2>nul | find "%OLD_PID%" >nul
    if not errorlevel 1 (
      echo Останавливаем предыдущий запуск PID %OLD_PID% ...
      taskkill /PID %OLD_PID% /T /F >nul 2>&1
      timeout /t 1 /nobreak >nul
    )
  )
  del /f /q "runtime\app.pid" >nul 2>&1
)

echo Запуск приложения...
start "GermanWindowsAI" /D "%~dp0app" "%~dp0app\GermanWindowsAI.exe"

echo Ожидание готовности сервиса...
set /a TRIES=0

:wait_loop
set /a TRIES+=1
if %TRIES% GTR 150 (
  echo.
  echo [ОШИБКА] Сервис не ответил за разумное время.
  echo Первый запуск может занять до 1–2 минут.
  echo Проверьте runtime\logs\app.log
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$port='8000'; if (Test-Path 'runtime\port.txt') { $port=(Get-Content 'runtime\port.txt' -Raw).Trim() }; try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Uri ('http://127.0.0.1:'+$port+'/api/health'); if ($r.StatusCode -eq 200) { Write-Output $port; exit 0 } else { exit 1 } } catch { exit 1 }" > "%TEMP%\leadassign_port.txt" 2>nul

if errorlevel 1 (
  timeout /t 1 /nobreak >nul
  goto wait_loop
)

set /p PORT=<"%TEMP%\leadassign_port.txt"
if not defined PORT set PORT=8000
if exist "runtime\port.txt" set /p PORT=<"runtime\port.txt"

echo Сервис готов: http://127.0.0.1:%PORT%/
echo Браузер должен открыться автоматически.
echo Если нет — откройте ссылку вручную.
echo.
echo Для остановки используйте ОСТАНОВИТЬ_ДЕМО.bat
echo.
pause
endlocal
