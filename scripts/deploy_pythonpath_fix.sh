#!/bin/bash
# Deploy PYTHONPATH fix to production server
# Date: 2025-10-03
# Agent: Deployment Manager

set -e

echo "========================================="
echo "PYTHONPATH Fix Deployment"
echo "========================================="
echo ""

SERVER="5.35.88.251"
USER="root"
PROJECT_PATH="/var/GrantService"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Backup current systemd service file${NC}"
ssh ${USER}@${SERVER} "sudo cp /etc/systemd/system/grantservice-admin.service /etc/systemd/system/grantservice-admin.service.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✓ Backup created${NC}"
echo ""

echo -e "${YELLOW}Step 2: Update systemd service with PYTHONPATH${NC}"
ssh ${USER}@${SERVER} "sudo sed -i '/\\[Service\\]/a Environment=\"PYTHONPATH=${PROJECT_PATH}:${PROJECT_PATH}/web-admin:${PROJECT_PATH}/data:${PROJECT_PATH}/telegram-bot:${PROJECT_PATH}/agents:${PROJECT_PATH}/shared\"' /etc/systemd/system/grantservice-admin.service"
echo -e "${GREEN}✓ PYTHONPATH added to service file${NC}"
echo ""

echo -e "${YELLOW}Step 3: Reload systemd daemon${NC}"
ssh ${USER}@${SERVER} "sudo systemctl daemon-reload"
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"
echo ""

echo -e "${YELLOW}Step 4: Restart grantservice-admin service${NC}"
ssh ${USER}@${SERVER} "sudo systemctl restart grantservice-admin"
echo -e "${GREEN}✓ Service restarted${NC}"
echo ""

echo -e "${YELLOW}Step 5: Verify service status${NC}"
ssh ${USER}@${SERVER} "sudo systemctl status grantservice-admin --no-pager -l" || true
echo ""

echo -e "${YELLOW}Step 6: Check for import errors in logs (last 50 lines)${NC}"
ssh ${USER}@${SERVER} "sudo journalctl -u grantservice-admin -n 50 --no-pager" || true
echo ""

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Monitor logs: sudo journalctl -u grantservice-admin -f"
echo "2. Check Admin Panel: http://5.35.88.251:8550"
echo "3. Verify no ModuleNotFoundError in logs"
