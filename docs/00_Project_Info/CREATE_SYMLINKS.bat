@echo off
REM Iteration 36: Create Symlinks for Methodology
REM Run as Administrator!

echo Creating symlinks for GrantService_Project...

REM Create Methodology symlink
mklink /D "C:\SnowWhiteAI\GrantService_Project\00_Project_Info\Methodology" "C:\SnowWhiteAI\cradle\01-Active-Projects\Project-Evolution-Methodology"

REM Create Exchange symlink
mklink /D "C:\SnowWhiteAI\GrantService_Project\00_Project_Info\Exchange" "C:\SnowWhiteAI\Exchange\GrantService_Project"

echo.
echo Done! Symlinks created.
echo.
pause
