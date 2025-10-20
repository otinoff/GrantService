#!/bin/bash
# Deploy Reference Points Framework V2 to Production
# Server: 5.35.88.251
# Date: 2025-10-20

set -e

echo "=========================================="
echo "🚀 DEPLOYING REFERENCE POINTS FRAMEWORK V2"
echo "=========================================="
echo ""

# Configuration
REPO_DIR="/var/GrantService"
SERVICE_NAME="grantservice-bot"
LOG_FILE="/var/log/grantservice-bot.log"

# Step 1: Pull latest code
echo "[1/5] Pulling latest code from GitHub..."
cd $REPO_DIR
git fetch origin
git pull origin master

echo "✅ Code updated"
echo ""

# Step 2: Check Python dependencies
echo "[2/5] Checking Python dependencies..."
if ! pip show qdrant-client > /dev/null 2>&1; then
    echo "Installing qdrant-client..."
    pip install qdrant-client
fi

echo "✅ Dependencies OK"
echo ""

# Step 3: Verify files
echo "[3/5] Verifying framework files..."
REQUIRED_FILES=(
    "agents/reference_points/__init__.py"
    "agents/reference_points/reference_point.py"
    "agents/reference_points/reference_point_manager.py"
    "agents/reference_points/adaptive_question_generator.py"
    "agents/reference_points/conversation_flow_manager.py"
    "agents/interactive_interviewer_agent_v2.py"
    "telegram-bot/telegram_interactive_interview.py"
    "telegram-bot/handlers/interactive_interview_handler.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$REPO_DIR/$file" ]; then
        echo "❌ Missing file: $file"
        exit 1
    fi
done

echo "✅ All files present"
echo ""

# Step 4: Check Qdrant connection
echo "[4/5] Checking Qdrant connection..."
QDRANT_STATUS=$(curl -s http://localhost:6333/healthz || echo "FAIL")
if [ "$QDRANT_STATUS" != "FAIL" ]; then
    echo "✅ Qdrant is running"

    # Check collection
    COLLECTION_CHECK=$(curl -s http://localhost:6333/collections/knowledge_sections | grep -o '"status":"green"' || echo "NO_COLLECTION")
    if [ "$COLLECTION_CHECK" = "NO_COLLECTION" ]; then
        echo "⚠️  WARNING: knowledge_sections collection not found"
        echo "   Run: python load_fpg_to_production.py"
    else
        echo "✅ knowledge_sections collection OK"
    fi
else
    echo "❌ Qdrant is not running!"
    echo "   Start with: systemctl start qdrant"
    exit 1
fi
echo ""

# Step 5: Restart bot
echo "[5/5] Restarting Telegram bot..."
systemctl restart $SERVICE_NAME

# Wait for startup
sleep 3

# Check status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Bot restarted successfully"
else
    echo "❌ Bot failed to start"
    echo ""
    echo "Check logs:"
    echo "  tail -f $LOG_FILE"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETED"
echo "=========================================="
echo ""
echo "📊 Next steps:"
echo "  1. Check logs: tail -f $LOG_FILE"
echo "  2. Test in Telegram: /start_interview_v2"
echo "  3. Monitor performance"
echo ""
echo "📝 Version info:"
git log -1 --oneline
echo ""
