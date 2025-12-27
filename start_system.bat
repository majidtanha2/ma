@echo off
chcp 65001
cls

echo ==========================================
echo    Trader's Guardian System - Startup
echo ==========================================
echo.

REM بررسی وجود پایتون
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM نصب کتابخانه‌ها اگر نیاز باشد
echo 📦 Checking Python packages...
pip install -r requirements.txt --quiet

REM ایجاد دایرکتوری‌ها
echo 📁 Creating directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "data\signals" mkdir data\signals
if not exist "data\analysis" mkdir data\analysis
if not exist "data\stats" mkdir data\stats
if not exist "shared_files" mkdir shared_files
if not exist "config" mkdir config

REM بررسی فایل تنظیمات
if not exist "config\settings.yaml" (
    echo ⚠️ Configuration file not found. Creating default...
    copy "config\settings.yaml.example" "config\settings.yaml" >nul
)

REM شروع سیستم
echo 🚀 Starting Trader's Guardian System...
echo.

REM اجرای سیستم اصلی
python python_backend\main.py

if errorlevel 1 (
    echo ❌ System failed to start!
    pause
    exit /b 1
)

echo.
echo ✅ System started successfully!
pause