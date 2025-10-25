#!/bin/bash
# Comprehensive Test Suite Runner for GrantService

set -e  # Exit on error

echo "====================================="
echo "  GrantService Test Suite Runner    "
echo "====================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check dependencies
echo "Step 1: Checking dependencies..."
if python -c "import pytest" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} pytest installed"
else
    echo -e "${RED}✗${NC} pytest not found. Installing..."
    pip install pytest pytest-asyncio pytest-mock pytest-cov
fi

if python -c "import telegram" 2>/dev/null; then
    VERSION=$(python -c "import telegram; print(telegram.__version__)")
    echo -e "${GREEN}✓${NC} python-telegram-bot installed (version: $VERSION)"

    # Check version
    MAJOR=$(echo $VERSION | cut -d. -f1)
    if [ "$MAJOR" -lt 20 ]; then
        echo -e "${YELLOW}⚠${NC}  Warning: python-telegram-bot version < 20. Consider upgrading."
    fi
else
    echo -e "${RED}✗${NC} python-telegram-bot not found"
fi

echo ""

# 2. Run linting (optional, if tools available)
echo "Step 2: Code quality checks..."
if command -v flake8 &> /dev/null; then
    echo "Running flake8..."
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
else
    echo -e "${YELLOW}⚠${NC}  flake8 not installed, skipping linting"
fi

echo ""

# 3. Run unit tests
echo "Step 3: Running unit tests..."
if [ -d "tests/unit" ]; then
    pytest tests/unit/ -v --tb=short
    echo -e "${GREEN}✓${NC} Unit tests passed"
else
    echo -e "${YELLOW}⚠${NC}  No unit tests directory found"
fi

echo ""

# 4. Run integration tests
echo "Step 4: Running integration tests..."
if [ -d "tests/integration" ]; then
    pytest tests/integration/ -v --tb=short
    echo -e "${GREEN}✓${NC} Integration tests passed"
else
    echo -e "${YELLOW}⚠${NC}  No integration tests directory found"
fi

echo ""

# 5. Generate coverage report
echo "Step 5: Generating coverage report..."
pytest tests/ --cov=./ --cov-report=html --cov-report=term-missing

echo ""
echo -e "${GREEN}✓${NC} Coverage report generated: htmlcov/index.html"

echo ""

# 6. Performance metrics
echo "Step 6: Performance metrics..."
echo "Slowest 10 tests:"
pytest tests/ --durations=10 --quiet

echo ""

# Summary
echo "====================================="
echo "  Test Suite Complete!               "
echo "====================================="
echo ""
echo "Next steps:"
echo "  - View coverage: open htmlcov/index.html"
echo "  - Check for slow tests in output above"
echo "  - Review any failures or warnings"
