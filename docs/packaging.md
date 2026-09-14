# Упаковка portable-демо

## Цель

Работодатель: ZIP → распаковать → двойной клик `ЗАПУСТИТЬ_ДЕМО.bat` → браузер с Dashboard.  
Без установки Python, Node.js, npm, Git.

## Архитектура запуска

```
GermanWindowsAI.exe
 ├── FastAPI (/api/*)
 ├── Static frontend (SPA)
 ├── health check
 ├── выбор свободного порта
 ├── pid / port файлы в runtime/
 └── автооткрытие браузера
```

## Файлы runtime

- `runtime/app.pid` — PID процесса  
- `runtime/port.txt` — выбранный порт  
- `runtime/logs/` — логи  

## Лаунчеры

- `ЗАПУСТИТЬ_ДЕМО.bat` — portable  
- `ОСТАНОВИТЬ_ДЕМО.bat` — остановка по PID  
- `ЗАПУСТИТЬ_ДЕМО_ДЛЯ_РАЗРАБОТЧИКА.bat` — через локальный Python (запасной)

## Сборка

1. `npm run build` в `frontend/`  
2. Скопировать `frontend/dist` → `backend/static`  
3. `pyinstaller` → `GermanWindowsAI.exe`  
4. PDF для работодателя: `python scripts/build_employer_pdfs.py`  
5. Собрать ZIP: `packaging/assemble_employer_release.ps1`  

Актуальный архив: `LeadAssign_Nemetskie_Okna_Bel_FINAL_2026-09-14.zip`  
В корне ZIP — PDF `00_…`–`04_…` и `ЗАПУСТИТЬ_ДЕМО.bat`.  

## Ограничения Windows

Неподписанный EXE может вызвать SmartScreen.  
Интернет для работы демо не требуется.
