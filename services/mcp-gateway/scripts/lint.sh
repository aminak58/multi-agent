#!/bin/bash
# Code quality and linting script

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MCP Gateway Code Quality Check${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dev dependencies if needed
pip install -q flake8 black isort mypy pylint 2>/dev/null || true

ERRORS=0

# Black formatting check
echo -e "${YELLOW}Checking code formatting (black)...${NC}"
if black --check app/ tests/; then
    echo -e "${GREEN}✓ Code formatting OK${NC}"
else
    echo -e "${RED}✗ Code formatting issues found${NC}"
    echo "  Run: black app/ tests/"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# isort import sorting
echo -e "${YELLOW}Checking import sorting (isort)...${NC}"
if isort --check-only app/ tests/; then
    echo -e "${GREEN}✓ Import sorting OK${NC}"
else
    echo -e "${RED}✗ Import sorting issues found${NC}"
    echo "  Run: isort app/ tests/"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Flake8 linting
echo -e "${YELLOW}Running flake8 linter...${NC}"
if flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503; then
    echo -e "${GREEN}✓ Flake8 passed${NC}"
else
    echo -e "${RED}✗ Flake8 found issues${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# MyPy type checking
echo -e "${YELLOW}Running type checking (mypy)...${NC}"
if mypy app/ --ignore-missing-imports --no-strict-optional; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
else
    echo -e "${RED}✗ Type checking found issues${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Pylint
echo -e "${YELLOW}Running pylint...${NC}"
if pylint app/ --max-line-length=100 --disable=C0111,R0903,W0212 || [ $? -lt 4 ]; then
    echo -e "${GREEN}✓ Pylint passed${NC}"
else
    echo -e "${RED}✗ Pylint found issues${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All quality checks passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS issue(s)${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
