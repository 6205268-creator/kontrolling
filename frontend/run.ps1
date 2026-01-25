# Run frontend: SNT Uchet (static site with test data)
$ErrorActionPreference = "Stop"
$dir = $PSScriptRoot
$port = 3000

Write-Host "Serving: $dir"
Write-Host "Port: $port"
Write-Host ""

Start-Process python -ArgumentList "-m", "http.server", $port, "--directory", $dir -WindowStyle Normal

Start-Sleep -Seconds 2
$url = "http://localhost:$port"
Write-Host "Open in browser: $url"
Start-Process $url
Write-Host "Server runs in the Python window. Close it to stop."
