#!/bin/bash
# Setup Testing Environment for GrantService

set -e

echo "=========================================="
echo "  GrantService Test Environment Setup   "
echo "=========================================="
echo ""

# 1. Create virtual environment (if not exists)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# 2. Activate virtual environment
echo ""
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated (Unix/Mac)"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo "✓ Virtual environment activated (Windows)"
fi

# 3. Install testing dependencies
echo ""
echo "Installing testing dependencies..."
pip install --upgrade pip

# Core dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov

# Quality tools
pip install flake8 black isort

# Project dependencies (if requirements.txt exists)
if [ -f "requirements.txt" ]; then
    echo "Installing project dependencies..."
    pip install -r requirements.txt
    echo "✓ Project dependencies installed"
fi

# 4. Create test directories if not exist
echo ""
echo "Setting up test directories..."
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e
mkdir -p tests/fixtures

echo "✓ Test directories created"

# 5. Create conftest.py if not exists
if [ ! -f "tests/conftest.py" ]; then
    echo ""
    echo "Creating tests/conftest.py..."
    cat > tests/conftest.py << 'EOF'
"""
pytest configuration and shared fixtures
"""
import pytest
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure asyncio mode
def pytest_configure(config):
    config.option.asyncio_mode = "auto"

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": 12345,
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def sample_application_data():
    """Sample grant application data"""
    return {
        "title": "Test Project",
        "grant_fund": "Presidential Grants",
        "amount": 1000000,
        "description": "Test project description"
    }
EOF
    echo "✓ conftest.py created"
fi

# 6. Create pytest.ini if not exists
if [ ! -f "pytest.ini" ]; then
    echo ""
    echo "Creating pytest.ini..."
    cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
asyncio_mode = auto
EOF
    echo "✓ pytest.ini created"
fi

# 7. Create sample test file if tests are empty
if [ ! -f "tests/unit/test_example.py" ]; then
    echo ""
    echo "Creating example test file..."
    cat > tests/unit/test_example.py << 'EOF'
"""
Example test file demonstrating testing patterns
"""
import pytest

def test_example():
    """Example test - always passes"""
    assert 1 + 1 == 2

@pytest.mark.asyncio
async def test_async_example():
    """Example async test"""
    async def async_add(a, b):
        return a + b

    result = await async_add(2, 3)
    assert result == 5

def test_with_fixture(sample_user_data):
    """Example test using fixture from conftest.py"""
    assert sample_user_data["username"] == "testuser"
EOF
    echo "✓ Example test created"
fi

# 8. Verify setup
echo ""
echo "Verifying installation..."
pytest --version
python -c "import telegram; print(f'python-telegram-bot: {telegram.__version__}')"

echo ""
echo "=========================================="
echo "  Setup Complete!                        "
echo "=========================================="
echo ""
echo "Environment ready. Next steps:"
echo "  1. Run tests: pytest"
echo "  2. Run with coverage: pytest --cov=./"
echo "  3. Or use: bash scripts/run_tests.sh"
echo ""
echo "To activate environment in future sessions:"
echo "  source venv/bin/activate  (Unix/Mac)"
echo "  venv\\Scripts\\activate    (Windows)"
