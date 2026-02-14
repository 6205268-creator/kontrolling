# Запуск BPMN Viewer с сохранением в проект
# Использование: .\run-bpmn-server.ps1

$port = 8888

# Останавливаем процесс, занимающий порт 8888
$conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($conn) {
    $pid = $conn.OwningProcess | Select-Object -First 1
    if ($pid) {
        Write-Host "Останавливаю процесс на порту $port (PID: $pid)..."
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

# Запускаем server.py
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
Write-Host "Запуск BPMN сервера..."
python server.py
