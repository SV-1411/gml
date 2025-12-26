#!/bin/bash
# Complete Route Verification and Fix Script

set -e

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "========================================="
echo "Route Verification and Fix Script"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Verify route files exist
echo "1. Checking route files..."
if [ -f "src/gml/api/routes/storage.py" ]; then
    echo -e "${GREEN}   ✅ storage.py exists${NC}"
else
    echo -e "${RED}   ❌ storage.py NOT FOUND${NC}"
    exit 1
fi

if [ -f "src/gml/api/routes/agents.py" ]; then
    echo -e "${GREEN}   ✅ agents.py exists${NC}"
else
    echo -e "${RED}   ❌ agents.py NOT FOUND${NC}"
    exit 1
fi

# Step 2: Check route definitions
echo ""
echo "2. Checking route definitions..."
if grep -q "@router.post" "src/gml/api/routes/storage.py" && grep -q '"/upload"' "src/gml/api/routes/storage.py"; then
    echo -e "${GREEN}   ✅ Upload route defined in storage.py${NC}"
else
    echo -e "${RED}   ❌ Upload route NOT found in storage.py${NC}"
    exit 1
fi

if grep -q "@router.patch" "src/gml/api/routes/agents.py" && grep -q "/status" "src/gml/api/routes/agents.py"; then
    echo -e "${GREEN}   ✅ Status route defined in agents.py${NC}"
else
    echo -e "${RED}   ❌ Status route NOT found in agents.py${NC}"
    exit 1
fi

# Step 3: Check route exports
echo ""
echo "3. Checking route exports..."
if grep -q "storage_router" "src/gml/api/routes/__init__.py"; then
    echo -e "${GREEN}   ✅ storage_router exported in __init__.py${NC}"
else
    echo -e "${RED}   ❌ storage_router NOT exported${NC}"
    exit 1
fi

# Step 4: Check route registration
echo ""
echo "4. Checking route registration..."
if grep -q "storage_router" "src/gml/api/main.py" && grep -q "app.include_router(storage_router" "src/gml/api/main.py"; then
    echo -e "${GREEN}   ✅ storage_router registered in main.py${NC}"
else
    echo -e "${RED}   ❌ storage_router NOT registered in main.py${NC}"
    exit 1
fi

# Step 5: Clear cache
echo ""
echo "5. Clearing Python cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}   ✅ Cache cleared${NC}"

# Step 6: Check if server is running
echo ""
echo "6. Checking if server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}   ⚠️  Server is running${NC}"
    echo -e "${YELLOW}   ⚠️  Checking if routes are loaded...${NC}"
    
    # Check if storage route is available
    if curl -s http://localhost:8000/api/openapi.json | grep -q "storage/upload" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Storage route is loaded in running server${NC}"
        echo ""
        echo -e "${GREEN}✅ All checks passed! Routes should be working.${NC}"
    else
        echo -e "${RED}   ❌ Storage route NOT found in running server${NC}"
        echo ""
        echo -e "${RED}=========================================${NC}"
        echo -e "${RED}ACTION REQUIRED: RESTART SERVER${NC}"
        echo -e "${RED}=========================================${NC}"
        echo ""
        echo "The route code is correct, but the server hasn't loaded it yet."
        echo ""
        echo "To fix:"
        echo "1. Stop the server (Ctrl+C in the terminal running uvicorn)"
        echo "2. Restart it with:"
        echo "   cd src"
        echo "   uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
        echo ""
        echo "3. After restart, verify routes at: http://localhost:8000/api/docs"
        exit 1
    fi
else
    echo -e "${YELLOW}   ⚠️  Server is not running${NC}"
    echo ""
    echo "To start the server:"
    echo "  cd src"
    echo "  uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "Then verify routes at: http://localhost:8000/api/docs"
fi

# Step 7: Test endpoint (if server is running)
echo ""
echo "7. Testing upload endpoint..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "test content" > /tmp/test_upload.txt 2>/dev/null || echo "test" > /tmp/test_upload.txt
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/storage/upload \
        -F "file=@/tmp/test_upload.txt" \
        -F "bucket=uploads" 2>&1)
    
    if echo "$RESPONSE" | grep -q "url" && echo "$RESPONSE" | grep -q "key"; then
        echo -e "${GREEN}   ✅ Upload endpoint is working!${NC}"
        echo "   Response: $RESPONSE" | head -c 200
        echo ""
        rm -f /tmp/test_upload.txt
    elif echo "$RESPONSE" | grep -q "not found\|404"; then
        echo -e "${RED}   ❌ Endpoint returns 404 - Route not loaded!${NC}"
        echo -e "${RED}   Response: $RESPONSE${NC}"
        echo ""
        echo -e "${RED}You MUST restart the server!${NC}"
        exit 1
    else
        echo -e "${YELLOW}   ⚠️  Unexpected response: $RESPONSE${NC}"
    fi
    rm -f /tmp/test_upload.txt
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Verification Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"

