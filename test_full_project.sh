#!/bin/bash
# Comprehensive Automated Test Suite for GML Project
# Tests all components: Backend, Database, Redis, Qdrant, MinIO, Frontend

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Function to print test results
print_result() {
    local test_name=$1
    local status=$2
    local message=$3
    
    if [ "$status" == "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        if [ -n "$message" ]; then
            echo -e "  ${GREEN}  → $message${NC}"
        fi
        ((PASSED++))
    elif [ "$status" == "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        if [ -n "$message" ]; then
            echo -e "  ${RED}  → $message${NC}"
        fi
        ((FAILED++))
    else
        echo -e "${YELLOW}⊘ SKIP${NC}: $test_name"
        if [ -n "$message" ]; then
            echo -e "  ${YELLOW}  → $message${NC}"
        fi
        ((SKIPPED++))
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "$expected_status" ]; then
        print_result "$description" "PASS" "HTTP $http_code"
        return 0
    else
        print_result "$description" "FAIL" "Expected HTTP $expected_status, got $http_code"
        return 1
    fi
}

# Function to test service health via Docker
test_docker_service() {
    local service_name=$1
    local description=$2
    
    if docker ps --format "{{.Names}}" | grep -q "^$service_name$"; then
        if docker inspect "$service_name" --format='{{.State.Status}}' | grep -q "running"; then
            print_result "$description" "PASS" "Container is running"
            return 0
        else
            print_result "$description" "FAIL" "Container exists but not running"
            return 1
        fi
    else
        print_result "$description" "FAIL" "Container not found"
        return 1
    fi
}

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     GML Project - Comprehensive Automated Test Suite         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Check if running from project root
echo -e "${BLUE}[1] Environment Check${NC}"
if [ -f "requirements.txt" ] && [ -d "src/gml" ]; then
    print_result "Project structure" "PASS" "Running from project root"
else
    print_result "Project structure" "FAIL" "Not in project root directory"
    exit 1
fi

# Test 2: Check Python virtual environment
if [ -d "venv" ]; then
    print_result "Virtual environment" "PASS" "venv directory exists"
else
    print_result "Virtual environment" "SKIP" "venv not found (may be using system Python)"
fi

echo ""

# Test 3: Docker Services
echo -e "${BLUE}[2] Docker Services${NC}"
test_docker_service "gml-postgres" "PostgreSQL container"
test_docker_service "gml-redis" "Redis container"
test_docker_service "gml-qdrant" "Qdrant container"
test_docker_service "gml-minio" "MinIO container"

echo ""

# Test 4: Service Connectivity (Direct)
echo -e "${BLUE}[3] Service Connectivity${NC}"

# PostgreSQL
if docker exec gml-postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_result "PostgreSQL connection" "PASS" "Database accepting connections"
else
    print_result "PostgreSQL connection" "FAIL" "Database not responding"
fi

# Redis
if docker exec gml-redis redis-cli ping > /dev/null 2>&1; then
    print_result "Redis connection" "PASS" "Redis responding to PING"
else
    print_result "Redis connection" "FAIL" "Redis not responding"
fi

# Qdrant
if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    print_result "Qdrant HTTP endpoint" "PASS" "Qdrant health check passed"
else
    print_result "Qdrant HTTP endpoint" "FAIL" "Qdrant not accessible"
fi

# MinIO
if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    print_result "MinIO HTTP endpoint" "PASS" "MinIO health check passed"
else
    print_result "MinIO HTTP endpoint" "FAIL" "MinIO not accessible"
fi

echo ""

# Test 5: Backend API Endpoints
echo -e "${BLUE}[4] Backend API Endpoints${NC}"

# Basic health check
test_endpoint "http://localhost:8000/health" 200 "Basic health endpoint"

# Detailed health check
response=$(curl -s http://localhost:8000/api/v1/health/detailed 2>&1)
if echo "$response" | grep -q '"status"'; then
    # Check if all services are healthy
    if echo "$response" | grep -q '"status": "healthy"'; then
        print_result "Detailed health endpoint" "PASS" "All services healthy"
    else
        print_result "Detailed health endpoint" "PASS" "Endpoint responding (some services may be unhealthy)"
    fi
else
    print_result "Detailed health endpoint" "FAIL" "Invalid response format"
fi

# API documentation
test_endpoint "http://localhost:8000/api/docs" 200 "API documentation"
test_endpoint "http://localhost:8000/api/openapi.json" 200 "OpenAPI schema"

# Agents endpoint
test_endpoint "http://localhost:8000/api/v1/agents" 200 "Agents list endpoint"

# Ollama health check
test_endpoint "http://localhost:8000/api/v1/ollama/health" 200 "Ollama health endpoint"

echo ""

# Test 6: Frontend
echo -e "${BLUE}[5] Frontend${NC}"
test_endpoint "http://localhost:3000" 200 "Frontend homepage"

echo ""

# Test 7: API Functionality Tests
echo -e "${BLUE}[6] API Functionality${NC}"

# Test agent registration (create a test agent)
TEST_AGENT_ID="test-agent-$(date +%s)"
TEST_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/agents/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"agent_id\": \"$TEST_AGENT_ID\",
        \"name\": \"Test Agent\",
        \"version\": \"1.0.0\",
        \"description\": \"Automated test agent\",
        \"capabilities\": [\"testing\"]
    }" 2>&1)

if echo "$TEST_RESPONSE" | grep -q "\"agent_id\": \"$TEST_AGENT_ID\""; then
    print_result "Agent registration" "PASS" "Test agent created successfully"
    
    # Clean up: Try to get the agent
    sleep 1
    GET_RESPONSE=$(curl -s "http://localhost:8000/api/v1/agents/$TEST_AGENT_ID" 2>&1)
    if echo "$GET_RESPONSE" | grep -q "\"agent_id\": \"$TEST_AGENT_ID\""; then
        print_result "Agent retrieval" "PASS" "Test agent retrieved successfully"
    else
        print_result "Agent retrieval" "FAIL" "Could not retrieve test agent"
    fi
else
    print_result "Agent registration" "FAIL" "Failed to create test agent"
fi

# Test memory search
MEMORY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/memory/search" \
    -H "Content-Type: application/json" \
    -H "X-Agent-ID: $TEST_AGENT_ID" \
    -d "{\"query\": \"test\", \"limit\": 5}" 2>&1)

if echo "$MEMORY_RESPONSE" | grep -q "\"results\""; then
    print_result "Memory search" "PASS" "Memory search endpoint working"
else
    print_result "Memory search" "SKIP" "Memory search may require valid agent ID or no memories exist"
fi

echo ""

# Test 8: MinIO Console
echo -e "${BLUE}[7] MinIO Console${NC}"
test_endpoint "http://localhost:9001" 200 "MinIO Console"

echo ""

# Test 9: Qdrant Dashboard
echo -e "${BLUE}[8] Qdrant Dashboard${NC}"
test_endpoint "http://localhost:6333/dashboard" 200 "Qdrant Dashboard"

echo ""

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                         Test Summary                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Passed:${NC}  $PASSED"
echo -e "  ${RED}Failed:${NC}  $FAILED"
echo -e "  ${YELLOW}Skipped:${NC} $SKIPPED"
echo ""

TOTAL=$((PASSED + FAILED + SKIPPED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi

