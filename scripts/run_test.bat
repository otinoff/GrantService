@echo off
echo ========================================
echo   GrantService Streamlit Test Runner
echo   Testing Authorization System
echo ========================================
echo.

REM Переход в директорию скрипта
cd /d "%~dp0"

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Checking Streamlit installation...
pip show streamlit > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Streamlit is not installed
    echo Installing Streamlit...
    pip install streamlit
)

echo.
echo Starting test application...
echo.
echo ========================================
echo Test Credentials:
echo.
echo Admin:
echo   User ID: 123456789
echo   Token: e807f1fcf8
echo.
echo Editor:
echo   User ID: 987654321
echo   Token: b8c37e33de
echo.
echo Viewer:
echo   User ID: 555555555
echo   Token: 5d7b9adcbe
echo ========================================
echo.
echo Opening browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

REM Запуск Streamlit
streamlit run test_streamlit_simple.py --server.port 8501 --server.headless true

pause