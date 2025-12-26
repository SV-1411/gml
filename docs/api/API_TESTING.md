# API Testing Guide

This guide helps you test the GML Infrastructure backend API endpoints before running the dashboard.

## Prerequisites

- Backend server running on `http://localhost:8000`
- `curl` installed
- `jq` installed (optional, for JSON formatting)

## Quick Test Script

Run the automated test script:

```bash
# Make script executable (first time only)
chmod +x test-api.sh

# Run tests
./test-api.sh

# With authentication token
export AUTH_TOKEN=your_token_here
./test-api.sh
```

## Manual Testing

### 1. Health Check

```bash
# Basic health check
curl http://localhost:8000/health

# Expected: {"status":"healthy"} or similar
```

### 2. Detailed Health

```bash
# Detailed service health
curl http://localhost:8000/api/v1/health/detailed

# Expected: Detailed health information for all services
```

### 3. Prometheus Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics

# Expected: Prometheus-formatted metrics
```

### 4. Dashboard Metrics

```bash
# System metrics (may require authentication)
curl http://localhost:8000/api/v1/dashboard/metrics

# With authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/dashboard/metrics

# Expected: System health metrics (CPU, memory, disk, etc.)
```

### 5. List Agents

```bash
# List all agents (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/agents

# With pagination
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/agents?skip=0&limit=10"

# Expected: List of agents with pagination info
```

### 6. Dashboard Overview

```bash
# Dashboard overview statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/dashboard/overview

# Expected: Overview statistics (total agents, costs, etc.)
```

### 7. Costs

```bash
# List costs
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/costs

# With date range
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/costs?start_date=2024-01-01&end_date=2024-12-31"

# Expected: List of costs with pagination
```

### 8. Memory

```bash
# Search memory
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"test query","limit":10}' \
  http://localhost:8000/api/v1/memory/search

# Expected: Memory search results
```

### 9. Ollama Health

```bash
# Ollama health check
curl http://localhost:8000/api/v1/ollama/health

# Expected: Ollama service status
```

### 10. Ollama Models

```bash
# List available Ollama models
curl http://localhost:8000/api/v1/ollama/models

# Expected: List of available models
```

## Testing WebSocket Connection

### Using wscat (if installed)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws

# You should see connection confirmation
```

### Using Browser Console

```javascript
// Open browser console and run:
const socket = io('http://localhost:8000', {
  path: '/ws',
  transports: ['websocket']
});

socket.on('connect', () => {
  console.log('Connected to WebSocket');
});

socket.on('agent_status_changed', (data) => {
  console.log('Agent status changed:', data);
});

socket.on('metrics_updated', (data) => {
  console.log('Metrics updated:', data);
});
```

## Common Issues

### 401 Unauthorized

- **Issue**: Endpoint requires authentication
- **Solution**: Include `Authorization: Bearer YOUR_TOKEN` header
- **Get Token**: Register/login to get authentication token

### 404 Not Found

- **Issue**: Endpoint doesn't exist or wrong URL
- **Solution**: Check API documentation, verify endpoint path

### Connection Refused

- **Issue**: Backend server not running
- **Solution**: Start backend server on port 8000

### CORS Errors

- **Issue**: Cross-origin requests blocked
- **Solution**: Backend should allow CORS from frontend origin

## Expected Response Formats

### Health Check
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Agent List
```json
{
  "agents": [...],
  "total": 100,
  "limit": 10,
  "offset": 0,
  "has_more": true
}
```

### Metrics
```json
{
  "cpu": 45.2,
  "memory": 62.1,
  "disk": 71.5,
  "database": {
    "status": "healthy",
    "lastCheck": "2024-01-01T00:00:00Z"
  }
}
```

## Next Steps

Once all API endpoints are working:

1. ✅ Verify environment variables in `.env`
2. ✅ Start the dashboard: `npm run dev`
3. ✅ Check browser console for connection status
4. ✅ Verify WebSocket connection in Network tab

