@echo off
REM Set PostgreSQL environment
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=grantservice
set DB_USER=grantservice_user
set DB_PASSWORD=grant_secure_pass_2024

REM Run update script
python database\update_websearch_settings.py
