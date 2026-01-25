param(
  [string]$DatabaseUrl = $env:DATABASE_URL
)

if (-not $DatabaseUrl -or $DatabaseUrl.Trim().Length -eq 0) {
  $DatabaseUrl = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/snt_core"
}

$env:DATABASE_URL = $DatabaseUrl

Write-Host "DATABASE_URL=$env:DATABASE_URL"

Write-Host "1) Миграции Alembic..."
..\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "2) Seed тестовых данных..."
..\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); from scripts.seed import main; main()"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "3) Запуск API..."
..\.venv\Scripts\uvicorn.exe app.main:app --app-dir . --reload --port 8000

