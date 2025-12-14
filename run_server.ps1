param(
    [string]$Host = '127.0.0.1',
    [int]$Port = 8001
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$python = Join-Path $root ".venv\Scripts\python.exe"
$manage = Join-Path $root "manage.py"

if (-not (Test-Path $python)) {
    Write-Error "Python executable not found at $python. Ensure the virtualenv exists at `.venv` or change the script.`"
    exit 1
}
if (-not (Test-Path $manage)) {
    Write-Error "Could not find manage.py at $manage. Run this script from the project root."
    exit 1
}

Write-Host "Starting Django dev server at http://$Host`:$Port/ using: $python" -ForegroundColor Green
& $python $manage runserver "$Host`:$Port"
