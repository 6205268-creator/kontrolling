# Run backend v2 (API :8001) + frontend (site :3000). Opens browser.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "backend_snt_v2"
$frontend = Join-Path $root "frontend"

Set-Location $backend
$env:DATABASE_URL = "sqlite:///./snt_v2.db"
python scripts/init_db.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Starting API on :8001..."
Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--app-dir", ".", "--port", "8001" -WorkingDirectory $backend -WindowStyle Normal

Start-Sleep -Seconds 3
Write-Host "Starting frontend on :3000..."
Set-Location $frontend
Start-Process python -ArgumentList "-m", "http.server", "3000", "--directory", $frontend -WindowStyle Normal
Start-Sleep -Seconds 2
Write-Host "Opening http://localhost:3000"
Start-Process "http://localhost:3000"
Write-Host "Backend: :8001, Frontend: :3000. Close Python windows to stop."
