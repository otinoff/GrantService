#!/bin/bash
# ============================================================
# PRODUCTION WRITER DEPLOYMENT SCRIPT
# Server: 5.35.88.251 (Beget VPS)
# Date: 2025-10-24
# ============================================================

set -e  # Exit on error

echo "====================================="
echo "ProductionWriter Deployment"
echo "Server: 5.35.88.251"
echo "====================================="

# ============================================================
# STEP 1: Database Migration
# ============================================================

echo ""
echo "[Step 1/4] Applying database migration..."

# Backup database
BACKUP_FILE="database/backups/grantservice_backup_$(date +%Y%m%d_%H%M%S).sql"
echo "Creating backup: $BACKUP_FILE"
PGPASSWORD=$DB_PASSWORD pg_dump -h localhost -p 5434 -U grantservice -d grantservice > "$BACKUP_FILE"
echo "✓ Backup created"

# Apply migration
echo "Applying migration 014..."
PGPASSWORD=$DB_PASSWORD psql -h localhost -p 5434 -U grantservice -d grantservice \
  -f database/migrations/014_update_grants_for_production_writer.sql

echo "✓ Migration applied"

# ============================================================
# STEP 2: Install Dependencies
# ============================================================

echo ""
echo "[Step 2/4] Installing dependencies..."

source venv/bin/activate

# Install ProductionWriter dependencies
pip install -q -r requirements_production_writer.txt

echo "✓ Dependencies installed"

# ============================================================
# STEP 3: Verify ProductionWriter
# ============================================================

echo ""
echo "[Step 3/4] Verifying ProductionWriter..."

# Test import
python3 -c "
import sys
sys.path.insert(0, 'agents')
from production_writer import ProductionWriter
print('✓ ProductionWriter imported successfully')
"

# Check Qdrant connection
python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='5.35.88.251', port=6333)
collections = client.get_collections()
print('✓ Qdrant connected:', len(collections.collections), 'collections')
"

echo "✓ ProductionWriter verified"

# ============================================================
# STEP 4: Restart Services
# ============================================================

echo ""
echo "[Step 4/4] Restarting services..."

# Restart bot (if grant_handler.py is integrated)
sudo systemctl restart grantservice-bot || echo "⚠ Bot not restarted (handler not integrated yet)"

# Restart admin panel
sudo systemctl restart grantservice-admin || echo "⚠ Admin panel not restarted"

echo "✓ Services restarted"

# ============================================================
# Deployment Complete
# ============================================================

echo ""
echo "====================================="
echo "✅ ProductionWriter Deployed!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Integrate grant_handler.py into telegram-bot"
echo "2. Test manual generation: /generate_grant <anketa_id>"
echo "3. Monitor logs: journalctl -u grantservice-bot -f"
echo ""
echo "Database backup: $BACKUP_FILE"
echo ""
