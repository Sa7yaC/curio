param (
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$Username = "",
    [string]$Password = "",
    [int]$TenantId = 1,
    [switch]$SmokeTest
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$TestFile = Join-Path $ScriptDir "load_test.js"

$K6Args = @(
    "run",
    "-e", "BASE_URL=$BaseUrl",
    "-e", "K6_USERNAME=$Username",
    "-e", "K6_PASSWORD=$Password",
    "-e", "K6_TENANT_ID=$TenantId"
)

if ($SmokeTest) {
    Write-Host "Running 5-second smoke test..." -ForegroundColor Cyan
    $K6Args += @("--vus", "1", "--duration", "5s")
} else {
    Write-Host "Running full load test profile..." -ForegroundColor Green
}

$K6Args += $TestFile

Write-Host "Executing: k6 $($K6Args -join ' ')" -ForegroundColor Yellow
& k6 @K6Args
