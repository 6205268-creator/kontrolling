# Run backend_snt_v2: init_db (migrations + seed), then uvicorn on port 8001
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venv = Join-Path (Split-Path $root -Parent) ".venv"
$py = Join-Path $venv "Scripts\python.exe"
$uvicorn = Join-Path $venv "Scripts\uvicorn.exe"
if (-not (Test-Path $py)) { $py = "python" }
if (-not (Test-Path $uvicorn)) { $uvicorn = "uvicorn" }

$env:DATABASE_URL = "sqlite:///./snt_v2.db"
Set-Location $root

Write-Host "1) Init DB (migrations + seed)..."
if ($py -eq "python") {
    python scripts/init_db.py
} else {
    & $py scripts/init_db.py
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "2) Uvicorn on :8001..."
if ($uvicorn -eq "uvicorn") {
    python -m uvicorn app.main:app --app-dir . --reload --port 8001
} else {
    & $uvicorn app.main:app --app-dir . --reload --port 8001
}
