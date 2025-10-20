# Claude API Deployment Script for PowerShell
# Разворачивает Claude Code API Wrapper на удаленный сервер

param(
    [string]$ServerIP = "178.236.17.55",
    [string]$Username = "root",
    [string]$Password = "6P&hm4%HuFnL"
)

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Claude API Deployment - PowerShell Script" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: $ServerIP" -ForegroundColor Yellow
Write-Host "User: $Username" -ForegroundColor Yellow
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Проверка наличия архива
if (-not (Test-Path "claude-api-deployment.tar.gz")) {
    Write-Host "ERROR: claude-api-deployment.tar.gz not found!" -ForegroundColor Red
    Write-Host "Please ensure the deployment archive exists in the current directory." -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Copying deployment archive to server..." -ForegroundColor Green
Write-Host "Password: $Password" -ForegroundColor Yellow
Write-Host ""

# Используем scp для копирования
$scpCommand = "scp"
$scpArgs = @(
    "claude-api-deployment.tar.gz",
    "${Username}@${ServerIP}:/root/"
)

try {
    & $scpCommand $scpArgs
    if ($LASTEXITCODE -ne 0) {
        throw "SCP failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "ERROR: Failed to copy file to server" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "You can try manually:" -ForegroundColor Yellow
    Write-Host "scp claude-api-deployment.tar.gz ${Username}@${ServerIP}:/root/" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "[2/3] Extracting and preparing deployment..." -ForegroundColor Green

$sshCommands = @"
cd /opt && \
mkdir -p claude-api && \
cd claude-api && \
tar -xzf /root/claude-api-deployment.tar.gz && \
chmod +x quick-deploy.sh && \
echo 'Files extracted successfully'
"@

$sshArgs = @(
    "${Username}@${ServerIP}",
    $sshCommands
)

try {
    & ssh $sshArgs
    if ($LASTEXITCODE -ne 0) {
        throw "SSH command failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "ERROR: Failed to extract files on server" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/3] Running deployment script..." -ForegroundColor Green
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

$deployCommand = "cd /opt/claude-api && ./quick-deploy.sh"
$deployArgs = @(
    "${Username}@${ServerIP}",
    $deployCommand
)

try {
    & ssh $deployArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Deployment script failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "WARNING: Deployment script returned an error" -ForegroundColor Yellow
    Write-Host "You may need to check the server manually" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Connect to server: ssh ${Username}@${ServerIP}" -ForegroundColor White
    Write-Host "Check logs: docker-compose logs -f" -ForegroundColor White
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Deployment Process Completed!" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Information:" -ForegroundColor Yellow
Write-Host "  URL:     http://${ServerIP}:8000" -ForegroundColor White
Write-Host "  Docs:    http://${ServerIP}:8000/docs" -ForegroundColor White
Write-Host "  Health:  http://${ServerIP}:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "API Key:" -ForegroundColor Yellow
Write-Host "  1f79b062cf00b8d28546f5bd283dc59a1c6a7f9e9fe5a8e5ef25b0cc27aa0732" -ForegroundColor White
Write-Host ""
Write-Host "Test API:" -ForegroundColor Yellow
Write-Host '  curl http://178.236.17.55:8000/health' -ForegroundColor White
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Yellow
Write-Host "  Connect:  ssh ${Username}@${ServerIP}" -ForegroundColor White
Write-Host "  Logs:     docker-compose logs -f" -ForegroundColor White
Write-Host "  Restart:  docker-compose restart" -ForegroundColor White
Write-Host "  Stop:     docker-compose down" -ForegroundColor White
Write-Host ""
