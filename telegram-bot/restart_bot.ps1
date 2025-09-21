# PowerShell script to restart GrantService Telegram Bot
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  GrantService Telegram Bot Restart" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Set working directory
Set-Location "C:\SnowWhiteAI\GrantService\telegram-bot"
Write-Host "[1/4] Current directory: $(Get-Location)" -ForegroundColor Yellow

# Stop existing Python processes running the bot
Write-Host "[2/4] Stopping existing bot processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*main.py*" -or 
    $_.MainWindowTitle -like "GrantService Bot*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

# Find and activate virtual environment
Write-Host "[3/4] Looking for virtual environment..." -ForegroundColor Yellow
$venvPaths = @(
    "..\venv\Scripts\Activate.ps1",
    "..\.venv\Scripts\Activate.ps1",
    "venv\Scripts\Activate.ps1",
    ".venv\Scripts\Activate.ps1"
)

$activated = $false
foreach ($venvPath in $venvPaths) {
    if (Test-Path $venvPath) {
        Write-Host "Activating virtual environment: $venvPath" -ForegroundColor Green
        & $venvPath
        $activated = $true
        break
    }
}

if (-not $activated) {
    Write-Host "WARNING: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Continuing with system Python..." -ForegroundColor Yellow
}

# Check Python version
Write-Host ""
Write-Host "[4/4] Python version:" -ForegroundColor Yellow
python --version

# Start the bot
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Starting Telegram bot..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Run the bot
try {
    python main.py
}
catch {
    Write-Host "Error occurred: $_" -ForegroundColor Red
}
finally {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host "Bot has been stopped." -ForegroundColor Yellow
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}