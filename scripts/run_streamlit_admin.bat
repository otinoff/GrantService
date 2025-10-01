@echo off
echo ========================================
echo   GrantService Admin Panel
echo   Cross-platform version
echo ========================================
echo.

REM Переход в директорию проекта
cd /d "C:\SnowWhiteAI\GrantService"

echo Installing required packages...
pip install qrcode pillow requests streamlit python-dateutil

echo.
echo Starting Streamlit Admin Panel...
echo URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Запуск Streamlit из корня проекта
streamlit run streamlit_app.py --server.port 8501