# Открыть визуальную схему модели данных (vis-network) в браузере по умолчанию
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$htmlPath = Join-Path $scriptDir "schema-viewer.html"
if (Test-Path $htmlPath) {
  Start-Process $htmlPath
} else {
  Write-Error "Файл не найден: $htmlPath"
}
