@echo off
REM Rebuild portable EXE + release folder (developer machine)
chcp 65001 >nul
cd /d "%~dp0.."

echo [1/4] Frontend build...
cd frontend
call npm run build
cd ..

echo [2/4] Copy static...
if exist backend\static rmdir /s /q backend\static
xcopy /e /i /y frontend\dist backend\static >nul

echo [3/4] PyInstaller...
cd backend
set PYTHONPATH=%CD%
python -m PyInstaller GermanWindowsAI.spec --noconfirm
cd ..

echo [4/4] Assemble release...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0assemble_release.ps1"
echo Done.
pause
