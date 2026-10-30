param (
    [int]$Workers = 4,
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

$VenvPython = if (Test-Path (Join-Path $PSScriptRoot "venv\Scripts\python.exe")) {
    Join-Path $PSScriptRoot "venv\Scripts\python.exe"
} else {
    Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"
}

$VenvUvicorn = if (Test-Path (Join-Path $PSScriptRoot "venv\Scripts\uvicorn.exe")) {
    Join-Path $PSScriptRoot "venv\Scripts\uvicorn.exe"
} else {
    Join-Path $PSScriptRoot "..\venv\Scripts\uvicorn.exe"
}

if (-not (Test-Path $VenvUvicorn)) {
    Write-Host "Uvicorn not found in venv. Installing..." -ForegroundColor Yellow
    & $VenvPython -m pip install uvicorn
}

Write-Host "Starting Uvicorn ($Workers workers) on http://$($Host):$Port ..." -ForegroundColor Green
& $VenvUvicorn ecommerce_platform.asgi:application --host $Host --port $Port --workers $Workers
