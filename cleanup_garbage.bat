@echo off
REM Garbage Collection Script for GrantService
REM Date: 2025-10-12
REM WARNING: This script will DELETE files. Review .claude/gc_analysis_2025-10-12.md first!

echo.
echo ========================================
echo   GrantService Garbage Collection
echo ========================================
echo.
echo This script will clean up temporary files, test scripts, and cache.
echo Please review .claude/gc_analysis_2025-10-12.md before proceeding!
echo.
echo Choose cleanup level:
echo   [1] MINIMAL  - Only Python cache and .tmp files (~4 MB)
echo   [2] MEDIUM   - + test scripts and temporary data (~12 MB)
echo   [3] FULL     - + all temporary files and archive (~20 MB)
echo   [0] CANCEL   - Exit without changes
echo.

set /p choice="Enter your choice (0-3): "

if "%choice%"=="0" (
    echo Cancelled by user.
    goto :end
)

if "%choice%"=="1" goto :minimal
if "%choice%"=="2" goto :medium
if "%choice%"=="3" goto :full

echo Invalid choice. Exiting.
goto :end

:minimal
echo.
echo [MINIMAL CLEANUP]
echo.

REM Create backup list
echo Creating backup list...
git status --short > .claude\gc_backup_list_2025-10-12.txt

echo [1/3] Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [2/3] Removing .pyc files...
del /s /q *.pyc 2>nul

echo [3/3] Removing temporary files...
del /q .coverage 2>nul
del /q data\database\*.tmp.* 2>nul
del /q nul 2>nul
del /q nul- 2>nul

echo.
echo MINIMAL cleanup completed! (~4 MB freed)
goto :end

:medium
echo.
echo [MEDIUM CLEANUP]
echo.

REM Create backup list
echo Creating backup list...
git status --short > .claude\gc_backup_list_2025-10-12.txt

echo [1/8] Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [2/8] Removing .pyc files...
del /s /q *.pyc 2>nul

echo [3/8] Removing temporary files...
del /q .coverage 2>nul
del /q data\database\*.tmp.* 2>nul
del /q nul 2>nul
del /q nul- 2>nul

echo [4/8] Removing test scripts from root...
del /q test_*.py 2>nul
del /q check_active_answers.py 2>nul
del /q fix_claude_wrapper.py 2>nul

echo [5/8] Removing temporary SQL files...
del /q *.sql 2>nul

echo [6/8] Removing temporary TXT files...
del /q active_*.txt 2>nul
del /q sync_*.txt 2>nul
del /q *_export.txt 2>nul
del /q interview_test_output.txt 2>nul
del /q anketa_*.txt 2>nul
del /q VALERIA_PTSD_GRANT_E2E_TEST.txt 2>nul
del /q prod_questions.txt 2>nul

echo [7/8] Removing temporary JSON files...
del /q E2E_*.json 2>nul
del /q research_ekaterina.json 2>nul
del /q test_websearch_payload.json 2>nul

echo [8/8] Removing test PDF files...
del /q AUDIT_*.pdf 2>nul
del /q INTERVIEW_*.pdf 2>nul
del /q test_*.pdf 2>nul

echo.
echo MEDIUM cleanup completed! (~12 MB freed)
goto :end

:full
echo.
echo [FULL CLEANUP]
echo.

REM Create backup list
echo Creating backup list...
git status --short > .claude\gc_backup_list_2025-10-12.txt

echo [1/12] Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [2/12] Removing .pyc files...
del /s /q *.pyc 2>nul

echo [3/12] Removing temporary files...
del /q .coverage 2>nul
del /q data\database\*.tmp.* 2>nul
del /q nul 2>nul
del /q nul- 2>nul

echo [4/12] Removing test scripts from root...
del /q test_*.py 2>nul
del /q check_active_answers.py 2>nul
del /q fix_claude_wrapper.py 2>nul

echo [5/12] Removing temporary SQL files...
del /q *.sql 2>nul

echo [6/12] Removing temporary TXT files...
del /q active_*.txt 2>nul
del /q sync_*.txt 2>nul
del /q *_export.txt 2>nul
del /q interview_test_output.txt 2>nul
del /q anketa_*.txt 2>nul
del /q VALERIA_PTSD_GRANT_E2E_TEST.txt 2>nul
del /q prod_questions.txt 2>nul

echo [7/12] Removing temporary JSON files...
del /q E2E_*.json 2>nul
del /q research_ekaterina.json 2>nul
del /q test_websearch_payload.json 2>nul

echo [8/12] Removing test PDF files...
del /q AUDIT_*.pdf 2>nul
del /q INTERVIEW_*.pdf 2>nul
del /q test_*.pdf 2>nul

echo [9/12] Removing database utilities folder...
if exist database rd /s /q database

echo [10/12] Removing web-admin test files...
cd web-admin
del /q apply_migration_*.py 2>nul
del /q bulk_e2e_test.py 2>nul
del /q check_*.py 2>nul
del /q fix_*.py 2>nul
del /q test_*.py 2>nul
del /q update_scores.py 2>nul
del /q verify_*.py 2>nul
del /q view_*.py 2>nul
del /q *.txt 2>nul
del /q grant_*.txt 2>nul
del /q SAMPLE_GRANT_*.txt 2>nul
cd ..

echo [11/12] Removing one-time scripts...
del /q analyze_research_quality.py 2>nul
del /q convert_md_to_pdf.py 2>nul
del /q create_demo_word_comparison.py 2>nul
del /q create_grant_sql.py 2>nul
del /q demo_ab_research_export.py 2>nul
del /q export_*.py 2>nul
del /q generate_*.py 2>nul
del /q run_ekaterina_research_and_export.py 2>nul
del /q run_research_claude_code.py 2>nul
del /q simple_claude_wrapper.py 2>nul
del /q transfer_grant_to_prod.py 2>nul

echo [12/12] Archiving old agents...
if not exist agents\archive\agents-old-20251012 mkdir agents\archive\agents-old-20251012
if exist agents\251008 move /y agents\251008 agents\archive\agents-old-20251012\ >nul
if exist agents\auditor_agent_claude.py move /y agents\auditor_agent_claude.py agents\archive\agents-old-20251012\ >nul
if exist agents\researcher_agent_v2.py move /y agents\researcher_agent_v2.py agents\archive\agents-old-20251012\ >nul
if exist agents\reviewer_agent.py move /y agents\reviewer_agent.py agents\archive\agents-old-20251012\ >nul
if exist agents\writer_agent_v2.py move /y agents\writer_agent_v2.py agents\archive\agents-old-20251012\ >nul

echo.
echo FULL cleanup completed! (~20 MB freed)
echo.
echo Archiving .claude reports...
if not exist reports\archive\2025-10\sessions mkdir reports\archive\2025-10\sessions
if not exist reports\archive\2025-10\completed mkdir reports\archive\2025-10\completed
if not exist reports\archive\2025-10\quickstarts mkdir reports\archive\2025-10\quickstarts

move /y .claude\SESSION_SUMMARY_2025-10-*.md reports\archive\2025-10\sessions\ 2>nul
move /y .claude\*_COMPLETED_*.md reports\archive\2025-10\completed\ 2>nul
move /y .claude\WEBSEARCH_ARCHITECTURE_COMPLETE_*.md reports\archive\2025-10\completed\ 2>nul
move /y .claude\QUICK_START*.md reports\archive\2025-10\quickstarts\ 2>nul

echo Reports archived to reports\archive\2025-10\
goto :end

:end
echo.
echo ========================================
echo.
echo Cleanup completed!
echo.
echo Next steps:
echo   1. Run: git status
echo   2. Test: python launcher.py
echo   3. Review: .claude\gc_analysis_2025-10-12.md
echo.
echo Backup list saved to: .claude\gc_backup_list_2025-10-12.txt
echo.
pause
