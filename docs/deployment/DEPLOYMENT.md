# Deployment Guide

## Docker Deployment

### Build Docker Image

```bash
npm run docker:build
# or
docker build -t gml-dashboard .
```

### Run Container

```bash
npm run docker:run
# or
docker run -p 3000:80 gml-dashboard
```

### Docker Compose

```bash
npm run docker:compose
# or
docker-compose up -d
```

## Environment Variables

Create `.env.production` file:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
VITE_WS_PATH=/ws
```

Build with environment variables:

```bash
docker build --build-arg VITE_API_URL=http://api.example.com -t gml-dashboard .
```

## Production Build

```bash
npm run build
```

Output will be in `dist/` directory.

## Nginx Configuration

The `nginx.conf` includes:
- API proxy to backend
- WebSocket proxy
- Static file caching
- SPA routing fallback
- Security headers
- Gzip compression

## Health Checks

Health check endpoint: `http://localhost:3000/health`

## Deployment Checklist

- [ ] Set environment variables
- [ ] Build production bundle
- [ ] Test Docker image locally
- [ ] Configure nginx for your domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure backend API URL
- [ ] Test WebSocket connection
- [ ] Monitor logs and errors

## Kubernetes Deployment

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gml-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gml-dashboard
  template:
    metadata:
      labels:
        app: gml-dashboard
    spec:
      containers:
      - name: dashboard
        image: gml-dashboard:latest
        ports:
        - containerPort: 80
        env:
        - name: VITE_API_URL
          value: "http://api-service:8000"
```

