#!/bin/bash
# Quick PostgreSQL Connection Script (Linux/Mac)
# No password prompt - uses PGPASSWORD environment variable

echo "Connecting to PostgreSQL..."
echo "Host: localhost:5432"
echo "Database: grantservice"
echo "User: postgres"
echo ""

export PGPASSWORD=root
psql -h localhost -p 5432 -U postgres -d grantservice
