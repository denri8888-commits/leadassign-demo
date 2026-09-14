# Деплой LeadAssign на Vercel (через GitHub)

## Что получит работодатель

Публичную ссылку вида `https://leadassign-....vercel.app` — открыл в браузере и смотрит демо.

## Важно про Vercel

- Первый заход после паузы может занять **15–40 секунд** (cold start).
- Состояние в памяти: после «засыпания» демо-день создаётся заново.
- Это нормально для тестового демо, не для боевой CRM.

## Шаги (один раз)

### 1. GitHub

1. Зарегистрируйтесь / войдите на https://github.com  
2. Создайте **новый публичный** репозиторий, например `leadassign-demo` (без README).  
3. В Cursor / терминале из папки проекта:

```powershell
$env:Path = "C:\Program Files\Git\bin;" + $env:Path
cd "d:\тестовое"
git init -b main
git add -A
git commit -m "LeadAssign demo for Vercel"
git remote add origin https://github.com/<ВАШ_ЛОГИН>/leadassign-demo.git
git push -u origin main
```

### 2. Vercel

1. Войдите на https://vercel.com через GitHub.  
2. **Add New Project** → выберите репозиторий `leadassign-demo`.  
3. Framework: оставьте как в `vercel.json` (не Next.js).  
4. Root Directory: `.` (корень).  
5. Deploy.

После деплоя скопируйте URL и отправьте работодателю вместе с PDF.

## Локальная проверка сборки

```powershell
cd "d:\тестовое"
npm --prefix frontend ci
npm --prefix frontend run build
node scripts/copy_frontend_static.mjs
```

## Если деплой падает из‑за размера

Напишите мне — упростим зависимости или вынесем backend на Render, а на Vercel оставим только витрину.
