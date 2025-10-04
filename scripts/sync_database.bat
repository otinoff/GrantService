@echo off
REM Database Sync Script - Download production database (Windows)
REM Usage: scripts\sync_database.bat [--no-backup]

setlocal enabledelayedexpansion

REM Configuration
set SERVER=root@5.35.88.251
set REMOTE_DB=/var/GrantService/data/grantservice.db
set LOCAL_DB=data\grantservice.db
set BACKUP_DIR=data\backups

echo =========================================
echo Database Sync - Production to Local
echo =========================================
echo.

REM Check if no-backup flag
set NO_BACKUP=false
if "%1"=="--no-backup" set NO_BACKUP=true

REM Create backup directory
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Backup current local database
if exist "%LOCAL_DB%" (
    if "%NO_BACKUP%"=="false" (
        echo Creating backup of local database...

        REM Generate timestamp
        for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
        set "YYYY=!dt:~0,4!"
        set "MM=!dt:~4,2!"
        set "DD=!dt:~6,2!"
        set "HH=!dt:~8,2!"
        set "Min=!dt:~10,2!"
        set "Sec=!dt:~12,2!"
        set TIMESTAMP=!YYYY!!MM!!DD!_!HH!!Min!!Sec!

        set BACKUP_NAME=grantservice_backup_!TIMESTAMP!.db
        copy "%LOCAL_DB%" "%BACKUP_DIR%\!BACKUP_NAME!" >nul

        if !errorlevel! equ 0 (
            echo [OK] Backup created: %BACKUP_DIR%\!BACKUP_NAME!

            REM Get backup size
            for %%F in ("%BACKUP_DIR%\!BACKUP_NAME!") do set BACKUP_SIZE=%%~zF
            set /a BACKUP_SIZE_MB=!BACKUP_SIZE! / 1024 / 1024
            echo     Size: !BACKUP_SIZE_MB! MB
            echo.
        ) else (
            echo [ERROR] Failed to create backup
            exit /b 1
        )
    )
)

REM Download from server
echo Downloading database from production server...
echo Server: %SERVER%
echo Remote: %REMOTE_DB%
echo.

scp %SERVER%:%REMOTE_DB% %LOCAL_DB%

if %errorlevel% equ 0 (
    echo.
    echo [OK] Database downloaded successfully!

    REM Get database size
    for %%F in ("%LOCAL_DB%") do set DB_SIZE=%%~zF
    set /a DB_SIZE_MB=!DB_SIZE! / 1024 / 1024
    echo     Size: !DB_SIZE_MB! MB

    echo.
    echo =========================================
    echo Sync completed successfully!
    echo =========================================
) else (
    echo.
    echo [ERROR] Failed to download database
    echo Check SSH connection to server
    exit /b 1
)

REM Show backup info
if "%NO_BACKUP%"=="false" (
    if exist "%BACKUP_DIR%" (
        echo.
        dir /b "%BACKUP_DIR%\grantservice_backup_*.db" 2>nul | find /c /v "" > temp_count.txt
        set /p BACKUP_COUNT=<temp_count.txt
        del temp_count.txt

        echo Backups stored in: %BACKUP_DIR%
        echo Total backups: !BACKUP_COUNT!
        echo Tip: Clean old backups with: del %BACKUP_DIR%\grantservice_backup_*
    )
)

endlocal
