#!/bin/bash
# Test runner script for MCP Gateway

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MCP Gateway Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r ../requirements-dev.txt 2>/dev/null || true
else
    source venv/bin/activate
fi

# Parse arguments
TEST_TYPE=${1:-all}
COVERAGE=${2:-true}

echo -e "${GREEN}Test Type: $TEST_TYPE${NC}"
echo -e "${GREEN}Coverage: $COVERAGE${NC}"
echo ""

# Base pytest command
PYTEST_CMD="pytest -v"

# Add coverage if enabled
if [ "$COVERAGE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml"
fi

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        $PYTEST_CMD tests/ -m "not integration and not performance and not slow"
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        $PYTEST_CMD tests/ -m integration
        ;;
    performance)
        echo -e "${GREEN}Running performance tests...${NC}"
        $PYTEST_CMD tests/ -m performance
        ;;
    fast)
        echo -e "${GREEN}Running fast tests (no slow tests)...${NC}"
        $PYTEST_CMD tests/ -m "not slow and not performance"
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        $PYTEST_CMD tests/
        ;;
    *)
        echo -e "${RED}Invalid test type: $TEST_TYPE${NC}"
        echo "Usage: $0 [unit|integration|performance|fast|all] [true|false]"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"

    if [ "$COVERAGE" = "true" ]; then
        echo ""
        echo -e "${GREEN}Coverage report generated:${NC}"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
    fi
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Tests failed!${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
