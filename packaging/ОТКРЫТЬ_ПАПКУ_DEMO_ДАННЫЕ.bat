@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "data\demo" (
  echo [ОШИБКА] Папка data\demo не найдена.
  echo Убедитесь, что архив распакован полностью.
  pause
  exit /b 1
)
echo Открываем папку с демо-файлами для импорта...
explorer "%~dp0data\demo"
exit /b 0
