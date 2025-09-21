#!/bin/bash

echo "============================================================"
echo "                GRANTSERVICE ADMIN PANEL"
echo "============================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Test environment first
echo "Testing environment setup..."
if ! python3 launcher.py --test > /dev/null 2>&1; then
    echo "[WARNING] Environment test failed. Running detailed test..."
    echo ""
    python3 launcher.py --test
    echo ""
    echo "[!] Fix the issues above before launching"
    exit 1
fi

echo "Environment OK"
echo ""
echo "Launching admin panel..."
echo "URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo "============================================================"
echo ""

python3 launcher.py