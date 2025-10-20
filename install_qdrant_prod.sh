#!/bin/bash
# Quick install script for Qdrant on production server

set -e

echo "================================================================================"
echo "QDRANT INSTALLATION ON PRODUCTION SERVER"
echo "================================================================================"

echo ""
echo "Step 1: Creating data directory..."
mkdir -p /var/qdrant_storage
chmod 777 /var/qdrant_storage
echo "   ✅ Directory created: /var/qdrant_storage"

echo ""
echo "Step 2: Pulling Qdrant Docker image..."
docker pull qdrant/qdrant:latest
echo "   ✅ Image pulled"

echo ""
echo "Step 3: Starting Qdrant container..."
docker run -d \
  --name qdrant \
  --restart always \
  -p 6333:6333 \
  -p 6334:6334 \
  -v /var/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

echo "   ✅ Container started"

echo ""
echo "Step 4: Waiting for Qdrant to start (5 seconds)..."
sleep 5

echo ""
echo "Step 5: Testing Qdrant API..."
RESPONSE=$(curl -s http://localhost:6333/)
if [[ $RESPONSE == *"qdrant"* ]]; then
    echo "   ✅ Qdrant is running!"
    echo "   Response: $RESPONSE"
else
    echo "   ❌ Qdrant not responding"
    exit 1
fi

echo ""
echo "Step 6: Opening firewall port 6333..."
ufw allow 6333/tcp
echo "   ✅ Port 6333 opened"

echo ""
echo "Step 7: Verifying external access..."
PUBLIC_IP=$(curl -s ifconfig.me)
echo "   Server public IP: $PUBLIC_IP"
echo "   Test from external machine: curl http://$PUBLIC_IP:6333/"

echo ""
echo "================================================================================"
echo "✅ QDRANT INSTALLATION COMPLETE!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Test from local machine: curl http://5.35.88.251:6333/"
echo "  2. Load knowledge base: python expert_agent/load_fpg_knowledge.py"
echo "  3. Configure bot to use Qdrant"
echo ""
echo "Container info:"
docker ps | grep qdrant
echo ""
echo "================================================================================"
