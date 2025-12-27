# Trader's Guardian System - Installation Script
# Run as Administrator

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Trader's Guardian System Installer     " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>$null
if (-not $pythonVersion) {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later from: https://www.python.org/downloads/"
    pause
    exit 1
}
Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green

# Update pip
Write-Host "📦 Updating pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# Create directories
Write-Host "📁 Creating directory structure..." -ForegroundColor Yellow
$directories = @(
    "logs",
    "data",
    "data\signals",
    "data\analysis",
    "data\stats",
    "shared_files",
    "shared_files\signals",
    "shared_files\violations",
    "config",
    "dashboard\assets"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}

# Copy config if not exists
if (-not (Test-Path "config\settings.yaml")) {
    if (Test-Path "config\settings.yaml.example") {
        Copy-Item "config\settings.yaml.example" "config\settings.yaml"
        Write-Host "📄 Created default configuration file" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Configuration template not found" -ForegroundColor Yellow
    }
}

# Set permissions for shared files
Write-Host "🔒 Setting up permissions..." -ForegroundColor Yellow
$acl = Get-Acl "shared_files"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "Everyone",
    "Modify",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.SetAccessRule($accessRule)
Set-Acl "shared_files" $acl

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Installation completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit 'config\settings.yaml' with your MT5 credentials" -ForegroundColor White
Write-Host "2. Run 'start_system.bat' to start the system" -ForegroundColor White
Write-Host "3. Open browser to http://localhost:8501 for dashboard" -ForegroundColor White
Write-Host ""
Write-Host "For support, check the documentation." -ForegroundColor Gray
Write-Host "==========================================" -ForegroundColor Cyan

pause