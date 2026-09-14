$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$release = Join-Path $root "release_employer"
if (Test-Path $release) { Remove-Item -Recurse -Force $release }

New-Item -ItemType Directory -Force -Path `
  "$release\app", `
  "$release\docs", `
  "$release\data\demo", `
  "$release\runtime\logs" | Out-Null

Copy-Item "$root\backend\dist\GermanWindowsAI.exe" "$release\app\"
Copy-Item -Recurse "$root\backend\static" "$release\app\static"

Get-ChildItem "$root\packaging\*.bat" | Where-Object { $_.Name -ne "build_release.bat" } | ForEach-Object {
  Copy-Item $_.FullName -Destination $release
}
Copy-Item "$root\packaging\README_КАК_ЗАПУСКАТЬ.txt" "$release\README_КАК_ЗАПУСКАТЬ.txt"
Copy-Item "$root\README.md" "$release\README.md"

# Основные PDF (короткий набор)
Copy-Item "$root\docs\employer_pdf\00_Быстрый_старт.pdf" "$release\00_Быстрый_старт.pdf"
Copy-Item "$root\docs\employer_pdf\Быстрый_старт.pdf" "$release\Быстрый_старт.pdf"
Copy-Item "$root\docs\employer_pdf\01_Ответ_на_тестовое_задание.pdf" "$release\01_Ответ_на_тестовое_задание.pdf"
Copy-Item "$root\docs\employer_pdf\Ответ_на_тестовое_задание_LeadAssign.pdf" "$release\Ответ_на_тестовое_задание_LeadAssign.pdf"
Copy-Item "$root\docs\employer_pdf\02_Краткие_результаты_демо.pdf" "$release\02_Краткие_результаты_демо.pdf"
Copy-Item "$root\docs\employer_pdf\03_Техническая_инструкция.pdf" "$release\03_Техническая_инструкция.pdf"

Copy-Item "$root\packaging\ОТКРЫТЬ_ПАПКУ_DEMO_ДАННЫЕ.bat" "$release\ОТКРЫТЬ_ПАПКУ_DEMO_ДАННЫЕ.bat"

Copy-Item "$root\docs\test_task_answer.md" "$release\docs\" -ErrorAction SilentlyContinue
Copy-Item "$root\docs\assumptions.md" "$release\docs\" -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path "$release\data\demo" | Out-Null
Copy-Item "$root\data\demo\*" "$release\data\demo\" -Force
Set-Content "$release\runtime\logs\.gitkeep" ""

$date = Get-Date -Format "yyyy-MM-dd"
$zip = Join-Path $root ("LeadAssign_Nemetskie_Okna_Bel_FINAL_" + $date + ".zip")
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path "$release\*" -DestinationPath $zip -CompressionLevel Optimal
Write-Host ("Release ready: " + $zip)
Write-Host ("Size MB: " + [math]::Round((Get-Item $zip).Length / 1MB, 1))
