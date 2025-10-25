@echo off
REM Deploy Reference Points Framework V2 to Production
REM Run from local Windows machine

echo ==========================================
echo 🚀 DEPLOYING TO PRODUCTION
echo ==========================================
echo.

echo [INFO] Connecting to 5.35.88.251...
echo.

REM Deploy via SSH
ssh root@5.35.88.251 "cd /var/GrantService && git pull origin master && chmod +x deploy_v2_to_production.sh && ./deploy_v2_to_production.sh"

echo.
echo ==========================================
echo ✅ DEPLOYMENT COMPLETED
echo ==========================================
echo.
echo Next: Test in Telegram with /start_interview_v2
echo.
pause
