#!/bin/bash
# Test runner script for jRetireWise
# Runs unit, integration, and E2E tests

set -e

echo "=========================================="
echo "jRetireWise Test Suite"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in Docker or locally
if [ -f /.dockerenv ]; then
    DOCKER_ENV=true
    echo "Running in Docker environment"
else
    DOCKER_ENV=false
    echo "Running in local environment"
fi

# Determine how to run tests
if [ "$DOCKER_ENV" = true ]; then
    PYTEST_CMD="python -m pytest"
else
    PYTEST_CMD="docker-compose exec -T web python -m pytest"
fi

# Run unit tests
echo -e "\n${YELLOW}=== Running Unit Tests ===${NC}"
if $PYTEST_CMD tests/unit/ -v --tb=short; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
fi

# Run integration tests
echo -e "\n${YELLOW}=== Running Integration Tests ===${NC}"
if $PYTEST_CMD tests/integration/ -v --tb=short; then
    echo -e "${GREEN}✓ Integration tests passed${NC}"
else
    echo -e "${RED}✗ Integration tests failed${NC}"
    exit 1
fi

# Run E2E tests (only if --e2e flag is passed)
if [ "$1" = "--e2e" ]; then
    echo -e "\n${YELLOW}=== Running E2E Tests ===${NC}"
    if [ "$DOCKER_ENV" = false ]; then
        echo "Starting Docker environment for E2E tests..."
        docker-compose up -d
        sleep 5
    fi

    if $PYTEST_CMD tests/e2e/ -v --tb=short; then
        echo -e "${GREEN}✓ E2E tests passed${NC}"
    else
        echo -e "${RED}✗ E2E tests failed${NC}"
        exit 1
    fi
fi

echo -e "\n${GREEN}=========================================="
echo "All tests passed!"
echo "==========================================${NC}"
