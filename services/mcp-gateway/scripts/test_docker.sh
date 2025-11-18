#!/bin/bash
# Run tests in Docker environment

set -e

echo "========================================="
echo "Running MCP Gateway Tests in Docker"
echo "========================================="
echo ""

# Navigate to project root
cd "$(dirname "$0")/../../.."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Start dependencies
echo "Starting test dependencies..."
docker-compose up -d redis postgres

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Check Redis
echo "Checking Redis..."
docker-compose exec -T redis redis-cli -a ${REDIS_PASSWORD:-devpassword} ping || {
    echo "Redis not ready"
    exit 1
}

# Check PostgreSQL
echo "Checking PostgreSQL..."
docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER:-bot_user} || {
    echo "PostgreSQL not ready"
    exit 1
}

echo ""
echo "All dependencies ready!"
echo ""

# Build and run tests in container
echo "Building test container..."
docker-compose build mcp-gateway

echo ""
echo "Running tests..."
docker-compose run --rm mcp-gateway bash -c "
    pip install pytest pytest-asyncio pytest-cov httpx
    pytest tests/ -v --cov=app --cov-report=term-missing
"

TEST_EXIT_CODE=$?

# Cleanup
echo ""
echo "Cleaning up..."
docker-compose down

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ All tests passed in Docker!"
    exit 0
else
    echo ""
    echo "✗ Tests failed in Docker!"
    exit 1
fi
