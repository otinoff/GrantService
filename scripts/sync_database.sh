#!/bin/bash
# Database Sync Script - Download production database
# Usage: ./scripts/sync_database.sh [--no-backup]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVER="root@5.35.88.251"
REMOTE_DB="/var/GrantService/data/grantservice.db"
LOCAL_DB="./data/grantservice.db"
BACKUP_DIR="./data/backups"

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}Database Sync - Production to Local${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""

# Check if no-backup flag
NO_BACKUP=false
if [ "$1" == "--no-backup" ]; then
    NO_BACKUP=true
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup current local database
if [ -f "$LOCAL_DB" ] && [ "$NO_BACKUP" = false ]; then
    BACKUP_NAME="grantservice_backup_$(date +%Y%m%d_%H%M%S).db"
    echo -e "${YELLOW}Creating backup of local database...${NC}"
    cp "$LOCAL_DB" "$BACKUP_DIR/$BACKUP_NAME"
    echo -e "${GREEN}✓ Backup created: $BACKUP_DIR/$BACKUP_NAME${NC}"

    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
    echo -e "${GREEN}  Size: $BACKUP_SIZE${NC}"
    echo ""
fi

# Download from server
echo -e "${YELLOW}Downloading database from production server...${NC}"
echo -e "${YELLOW}Server: $SERVER${NC}"
echo -e "${YELLOW}Remote: $REMOTE_DB${NC}"
echo ""

scp "$SERVER:$REMOTE_DB" "$LOCAL_DB"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Database downloaded successfully!${NC}"

    # Get database size
    DB_SIZE=$(du -h "$LOCAL_DB" | cut -f1)
    echo -e "${GREEN}  Size: $DB_SIZE${NC}"

    # Get database stats (if sqlite3 available)
    if command -v sqlite3 &> /dev/null; then
        echo ""
        echo -e "${YELLOW}Database Statistics:${NC}"

        USERS_COUNT=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "N/A")
        SESSIONS_COUNT=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "N/A")
        ANKETAS_COUNT=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM anketas;" 2>/dev/null || echo "N/A")

        echo -e "${GREEN}  Users: $USERS_COUNT${NC}"
        echo -e "${GREEN}  Sessions: $SESSIONS_COUNT${NC}"
        echo -e "${GREEN}  Anketas: $ANKETAS_COUNT${NC}"
    fi

    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}Sync completed successfully!${NC}"
    echo -e "${GREEN}=========================================${NC}"
else
    echo ""
    echo -e "${RED}✗ Failed to download database${NC}"
    echo -e "${RED}Check SSH connection to server${NC}"
    exit 1
fi

# Show backup info
if [ "$NO_BACKUP" = false ] && [ -d "$BACKUP_DIR" ]; then
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)
    echo ""
    echo -e "${YELLOW}Backups stored in: $BACKUP_DIR${NC}"
    echo -e "${YELLOW}Total backups: $BACKUP_COUNT${NC}"
    echo -e "${YELLOW}Tip: Clean old backups with: rm $BACKUP_DIR/grantservice_backup_*${NC}"
fi
