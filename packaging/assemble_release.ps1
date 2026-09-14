$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (Test-Path "$root\release") { Remove-Item -Recurse -Force "$root\release" }
New-Item -ItemType Directory -Force -Path `
  "$root\release\app", `
  "$root\release\docs", `
  "$root\release\data\demo", `
  "$root\release\screenshots", `
  "$root\release\runtime\logs" | Out-Null

Copy-Item "$root\backend\dist\GermanWindowsAI.exe" "$root\release\app\"
Copy-Item -Recurse "$root\backend\static" "$root\release\app\static"
Copy-Item "$root\packaging\*.bat" "$root\release\"
Copy-Item "$root\packaging\README*.txt" "$root\release\"

Copy-Item "$root\docs\test_task_answer.md" "$root\release\docs\test_task_answer.md"
Copy-Item "$root\docs\architecture.md" "$root\release\docs\architecture.md"
Copy-Item "$root\docs\demo_script.md" "$root\release\docs\demo_script.md"
Copy-Item "$root\docs\assumptions.md","$root\docs\packaging.md","$root\docs\data_dictionary.md","$root\docs\project_summary.md" "$root\release\docs\"
if (Test-Path "$root\data\reports\test_assignment_fix_2026-09-13.md") {
  Copy-Item "$root\data\reports\test_assignment_fix_2026-09-13.md" "$root\release\docs\"
}
if (Test-Path "$root\data\reports\test_assignment_fix_2026-09-13.json") {
  Copy-Item "$root\data\reports\test_assignment_fix_2026-09-13.json" "$root\release\docs\"
}

Copy-Item "$root\data\demo_history.csv" "$root\release\data\demo\" -ErrorAction SilentlyContinue
Copy-Item "$root\data\demo_applications.csv" "$root\release\data\demo\" -ErrorAction SilentlyContinue
Set-Content -Encoding UTF8 "$root\release\screenshots\README.txt" "Screenshots optional."
Set-Content "$root\release\runtime\logs\.gitkeep" ""

$zip = Join-Path $root "LeadAssign_Nemetskie_Okna_Bel_FINAL_2026-09-13.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path "$root\release\*" -DestinationPath $zip -CompressionLevel Optimal
Write-Host ("Release ready: " + $zip)
