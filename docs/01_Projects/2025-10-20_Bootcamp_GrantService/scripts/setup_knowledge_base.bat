@echo off
REM Setup Sber500 Bootcamp Knowledge Base
REM Total time: ~3 minutes

echo ========================================
echo Sber500 Bootcamp Knowledge Base Setup
echo ========================================
echo.

echo Step 1/4: Creating collection...
python create_bootcamp_collection.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to create collection
    pause
    exit /b 1
)
echo.

echo Step 2/4: Adding initial documents (8 docs)...
python add_bootcamp_docs.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to add initial documents
    pause
    exit /b 1
)
echo.

echo Step 3/4: Adding token balance data (4 docs)...
python add_token_balance_data.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to add token balance data
    pause
    exit /b 1
)
echo.

echo Step 4/4: Adding bootcamp info (1 doc)...
python add_bootcamp_about.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to add bootcamp info
    pause
    exit /b 1
)
echo.

echo ========================================
echo SUCCESS! Knowledge base ready!
echo ========================================
echo.
echo Total documents: 13
echo - Email info
echo - Partner requirements
echo - Portal structure
echo - Token balance (6M GigaChat + 5M Embeddings)
echo - Strategy for TOP50
echo - Bootcamp details
echo.
echo Try searching:
echo   python search_bootcamp.py
echo.

pause
