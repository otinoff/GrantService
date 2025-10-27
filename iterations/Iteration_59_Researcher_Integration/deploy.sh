#!/bin/bash
# Iteration 59: Deployment Script
# Deploys Researcher Integration to Production

set -e  # Exit on error

echo "========================================================================"
echo "ITERATION 59: Deploying Researcher Integration"
echo "========================================================================"
echo ""

# Step 1: Update Production Database
echo "[1/5] Updating production database schema..."
echo ""

ssh root@5.35.88.251 << 'EOF'
cd /var/GrantService

echo "Adding research_data column to sessions table..."
PGPASSWORD=root psql -h localhost -U postgres -d grantservice -c "
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS research_data JSONB;
"

echo "Verifying column..."
PGPASSWORD=root psql -h localhost -U postgres -d grantservice -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'research_data';
"

echo "[OK] Database schema updated"
EOF

echo ""
echo "[2/5] Deploying code to production..."
echo ""

ssh root@5.35.88.251 << 'EOF'
cd /var/GrantService

echo "Pulling latest changes..."
git pull origin master

echo "[OK] Code deployed"
EOF

echo ""
echo "[3/5] Restarting bot service..."
echo ""

ssh root@5.35.88.251 << 'EOF'
systemctl restart grantservice-bot

echo "Waiting 5 seconds for service to start..."
sleep 5

systemctl status grantservice-bot --no-pager | head -20
EOF

echo ""
echo "[4/5] Checking logs for errors..."
echo ""

ssh root@5.35.88.251 << 'EOF'
echo "Last 20 log lines:"
journalctl -u grantservice-bot -n 20 --no-pager

echo ""
echo "Checking for errors in last minute..."
if journalctl -u grantservice-bot --since "1 minute ago" | grep -i "error\|exception\|fail" | grep -v "Failed to parse"; then
    echo "[WARNING] Errors found in logs!"
else
    echo "[OK] No critical errors found"
fi
EOF

echo ""
echo "========================================================================"
echo "[5/5] Deployment Summary"
echo "========================================================================"
echo ""
echo "  ✓ Database schema updated (research_data column)"
echo "  ✓ Code deployed (git pull)"
echo "  ✓ Bot service restarted"
echo "  ✓ Logs checked"
echo ""
echo "Next steps:"
echo "  1. Ask user to test full pipeline manually"
echo "  2. Monitor logs: ssh root@5.35.88.251 'journalctl -u grantservice-bot -f'"
echo "  3. Create SUCCESS.md if tests pass"
echo ""
echo "========================================================================"
echo "[SUCCESS] Iteration 59 Deployed to Production!"
echo "========================================================================"
echo ""
