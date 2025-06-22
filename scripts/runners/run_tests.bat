@echo off
REM Test Runner Script for Examtie Backend API (Windows)
REM This script runs comprehensive tests against the API

echo 🧪 Examtie Backend API Test Runner
echo ==================================

REM Check if the server is running
echo 🔍 Checking if server is running...
curl -s http://localhost:8000/ >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Server is running at http://localhost:8000
) else (
    echo ❌ Server is not running. Please start the server first with:
    echo    run_server.bat
    echo.
    echo 💡 To start the server in a separate window:
    echo    start run_server.bat
    exit /b 1
)

echo 📦 Installing test dependencies...
pip install requests

echo 🧪 Running comprehensive API tests...
python tests/test_comprehensive_admin.py

echo.
echo 📝 Additional test files available:
echo    - tests/test_admin.py (basic admin tests)
echo    - tests/test_bulk_admin.py (bulk operations tests)
echo    - tests/test_final_admin.py (final comprehensive tests)
echo.
echo 🔧 To run individual tests:
echo    python tests/test_admin.py
echo    python tests/test_bulk_admin.py
echo    python tests/test_final_admin.py
