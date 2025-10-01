@echo off
echo ========================================
echo   GrantService Admin Panel
echo   Cross-platform version
echo ========================================
echo.
echo Checking Python environment...
python --version

echo.
echo Installing dependencies if needed...
pip install -r requirements_streamlit.txt 2>nul

echo.
echo Starting admin panel from web-admin directory...
echo URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%~dp0\web-admin"
streamlit run main_admin.py --server.port 8501