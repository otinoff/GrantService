@echo off
REM Setup технической документации в Qdrant
REM Все пароли, API keys, команды

echo ========================================
echo Setup Technical Documentation в Qdrant
echo ========================================
echo.

echo Step 1/2: Creating collection...
python create_tech_docs_collection.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to create collection
    pause
    exit /b 1
)
echo.

echo Step 2/2: Adding technical documents...
python add_tech_docs.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to add documents
    pause
    exit /b 1
)
echo.

echo ========================================
echo SUCCESS! Tech docs ready!
echo ========================================
echo.
echo Total documents: 7
echo - PostgreSQL passwords
echo - API Keys (GigaChat, Perplexity)
echo - Commands (SSH, systemctl)
echo - Project structure
echo - Qdrant info
echo - Iterations history
echo - Bootcamp strategy
echo.
echo Try searching:
echo   python search_tech_docs.py "пароль базы"
echo   python search_tech_docs.py "api key"
echo   python search_tech_docs.py "как запустить"
echo.

pause
