# GML Project - Automated Test Suite

Comprehensive automated testing for all project components.

## Quick Start

### Python Test Suite (Recommended)
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
python3 test_full_project_python.py
```

### Bash Test Suite
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_full_project.sh
```

## Test Coverage

### [1] Environment Check
- ✅ Project structure validation
- ✅ Virtual environment detection

### [2] Docker Services
- ✅ PostgreSQL container (`gml-postgres`)
- ✅ Redis container (`gml-redis`)
- ✅ Qdrant container (`gml-qdrant`)
- ✅ MinIO container (`gml-minio`)

### [3] Service Connectivity
- ✅ PostgreSQL database connection
- ✅ Redis connection (PING test)
- ✅ Qdrant HTTP health endpoint
- ✅ MinIO HTTP health endpoint

### [4] Backend API Endpoints
- ✅ Basic health endpoint (`/health`)
- ✅ Detailed health endpoint (`/api/v1/health/detailed`)
- ✅ API documentation (`/api/docs`)
- ✅ OpenAPI schema (`/api/openapi.json`)
- ✅ Agents list endpoint (`/api/v1/agents`)
- ✅ Ollama health endpoint (`/api/v1/ollama/health`)

### [5] Frontend
- ✅ Frontend homepage (`http://localhost:3000`)

### [6] API Functionality
- ✅ Agent registration
- ✅ Agent retrieval
- ✅ Memory search

### [7] Web Interfaces
- ✅ MinIO Console (`http://localhost:9001`)
- ✅ Qdrant Dashboard (`http://localhost:6333/dashboard`)

## Test Results

Results are saved to `test_results.json` for analysis and reporting.

## Requirements

### Python Test Suite
- Python 3.7+
- `httpx` library (install with `pip install httpx`)

### Bash Test Suite
- `curl`
- `docker` CLI
- `bash` 4.0+

## Running Tests in CI/CD

```bash
# Install dependencies
pip install httpx

# Run tests
python3 test_full_project_python.py

# Check exit code (0 = all passed, 1 = some failed)
echo $?
```

## Expected Output

When all tests pass:
```
✓ All critical tests passed!
```

Test summary:
- **Passed**: 22
- **Failed**: 0
- **Skipped**: 0

## Troubleshooting

### Some tests fail
1. Ensure all Docker containers are running: `docker ps`
2. Check backend server is running: `curl http://localhost:8000/health`
3. Check frontend is running: `curl http://localhost:3000`
4. Review `test_results.json` for detailed error messages

### Docker services not found
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d
```

### Backend not responding
```bash
# Check if server is running
lsof -ti:8000

# Start server if needed
cd "/Volumes/Yatri Cloud/org/gml/project"
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
uvicorn src.gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run test suite
  run: |
    cd "/Volumes/Yatri Cloud/org/gml/project"
    python3 test_full_project_python.py
    
- name: Upload test results
  uses: actions/upload-artifact@v2
  if: always()
  with:
    name: test-results
    path: test_results.json
```

