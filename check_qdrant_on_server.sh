#!/bin/bash
# Check Qdrant installation and status on production server

echo "================================================================================"
echo "QDRANT CHECK ON PRODUCTION SERVER"
echo "================================================================================"

echo ""
echo "1. Checking Docker containers..."
docker ps -a | grep -i qdrant
QDRANT_RUNNING=$?

if [ $QDRANT_RUNNING -eq 0 ]; then
    echo "   ✅ Qdrant container found"
else
    echo "   ❌ No Qdrant container found"
fi

echo ""
echo "2. Checking if Qdrant is listening on port 6333..."
netstat -tlnp | grep 6333 || ss -tlnp | grep 6333
PORT_OPEN=$?

if [ $PORT_OPEN -eq 0 ]; then
    echo "   ✅ Port 6333 is open"
else
    echo "   ❌ Port 6333 is not listening"
fi

echo ""
echo "3. Checking Qdrant API (localhost)..."
curl -s http://localhost:6333/ | head -3

echo ""
echo "4. Listing Qdrant collections..."
curl -s http://localhost:6333/collections | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Collections: {len(data.get('result', {}).get('collections', []))}\"); [print(f\"  - {c['name']}: {c['points_count']} points\") for c in data.get('result', {}).get('collections', [])]"

echo ""
echo "5. Checking knowledge_sections collection..."
curl -s http://localhost:6333/collections/knowledge_sections | python3 -c "import sys, json; r=json.load(sys.stdin).get('result', {}); print(f\"  Status: {r.get('status')}\n  Points: {r.get('points_count')}\n  Vectors: {r.get('vectors_count')}\")"

echo ""
echo "6. Checking Qdrant data directory..."
ls -lah /var/qdrant_storage/ 2>/dev/null || ls -lah /opt/qdrant/ 2>/dev/null || echo "   ❌ Qdrant data dir not found"

echo ""
echo "7. Checking firewall rules for port 6333..."
ufw status | grep 6333 || iptables -L -n | grep 6333 || echo "   No firewall rules found"

echo ""
echo "================================================================================"
echo "RECOMMENDATIONS:"
echo "================================================================================"

if [ $QDRANT_RUNNING -ne 0 ]; then
    echo "❌ Qdrant NOT RUNNING - need to install/start it"
    echo ""
    echo "To install Qdrant:"
    echo "  docker run -d -p 6333:6333 -v /var/qdrant_storage:/qdrant/storage qdrant/qdrant"
else
    echo "✅ Qdrant is running"

    if [ $PORT_OPEN -ne 0 ]; then
        echo "⚠️  Port 6333 not accessible from outside"
        echo ""
        echo "To open port:"
        echo "  ufw allow 6333/tcp"
        echo "  # AND configure Qdrant to listen on 0.0.0.0 (not just localhost)"
    fi
fi

echo ""
echo "================================================================================"
