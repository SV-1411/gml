# Docker Compose Verification Guide

This guide provides commands to verify that all services in `docker-compose.dev.yml` are running correctly.

## Quick Verification

### Check Service Status

```bash
docker-compose -f docker-compose.dev.yml ps
```

Expected output should show all services as "Up" and "healthy":
- `gml-postgres` - Up (healthy)
- `gml-redis` - Up (healthy)
- `gml-qdrant` - Up (healthy)
- `gml-minio` - Up (healthy)
- `gml-minio-client` - Exited (0) - This is normal, it's a one-time setup job

### View Service Logs

```bash
# View logs for all services
docker-compose -f docker-compose.dev.yml logs

# View logs for a specific service
docker-compose -f docker-compose.dev.yml logs postgres
docker-compose -f docker-compose.dev.yml logs redis
docker-compose -f docker-compose.dev.yml logs qdrant
docker-compose -f docker-compose.dev.yml logs minio

# Follow logs in real-time
docker-compose -f docker-compose.dev.yml logs -f postgres
```

### Restart Services

```bash
# Stop all services
docker-compose -f docker-compose.dev.yml down

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Restart a specific service
docker-compose -f docker-compose.dev.yml restart postgres
```

## Detailed Service Verification

### PostgreSQL (Port 5432)

```bash
# Check if PostgreSQL is accepting connections
docker exec gml-postgres pg_isready -U postgres

# Connect to database
docker exec -it gml-postgres psql -U postgres -d gml_db

# Test query
docker exec gml-postgres psql -U postgres -d gml_db -c "SELECT version();"
```

### Redis (Port 6379)

```bash
# Test Redis connection
docker exec gml-redis redis-cli ping
# Expected: PONG

# Check Redis info
docker exec gml-redis redis-cli info server

# Test Redis operations
docker exec gml-redis redis-cli set test_key "test_value"
docker exec gml-redis redis-cli get test_key
```

### Qdrant (Ports 6333, 6334)

```bash
# Check Qdrant health
curl http://localhost:6333/healthz

# Check Qdrant collections
curl http://localhost:6333/collections

# Check Qdrant metrics
curl http://localhost:6333/metrics
```

### MinIO (Ports 9000, 9001)

```bash
# Check MinIO health
curl http://localhost:9000/minio/health/live

# Access MinIO console
# Open browser: http://localhost:9001
# Login: minioadmin / minioadmin

# List buckets using MinIO client
docker exec gml-minio-client /usr/bin/mc ls myminio/
```

## Port Conflict Check

Verify that ports are not already in use:

```bash
# Check PostgreSQL port
lsof -i :5432

# Check Redis port
lsof -i :6379

# Check Qdrant ports
lsof -i :6333
lsof -i :6334

# Check MinIO ports
lsof -i :9000
lsof -i :9001
```

If ports are in use, either:
1. Stop the conflicting service
2. Modify port mappings in `docker-compose.dev.yml`

## Health Check Verification

### Check Health Status

```bash
# View health status for all services
docker inspect gml-postgres | grep -A 10 Health
docker inspect gml-redis | grep -A 10 Health
docker inspect gml-qdrant | grep -A 10 Health
docker inspect gml-minio | grep -A 10 Health
```

### Manual Health Check Tests

```bash
# PostgreSQL
docker exec gml-postgres pg_isready -U postgres -d gml_db

# Redis
docker exec gml-redis redis-cli ping

# Qdrant
docker exec gml-qdrant wget --spider http://localhost:6333/healthz

# MinIO
docker exec gml-minio curl -f http://localhost:9000/minio/health/live
```

## Volume Verification

```bash
# List all volumes
docker volume ls | grep gml

# Inspect a volume
docker volume inspect gml-infrastructure_postgres_data
docker volume inspect gml-infrastructure_redis_data
docker volume inspect gml-infrastructure_qdrant_data
docker volume inspect gml-infrastructure_minio_data

# Check volume usage
docker system df -v
```

## Network Verification

```bash
# List networks
docker network ls | grep gml

# Inspect network
docker network inspect gml-infrastructure_gml-network

# Test connectivity between services
docker exec gml-postgres ping -c 3 redis
docker exec gml-redis ping -c 3 postgres
```

## ARM64 Compatibility Check

```bash
# Verify all containers are running on ARM64
docker inspect gml-postgres | grep Architecture
docker inspect gml-redis | grep Architecture
docker inspect gml-qdrant | grep Architecture
docker inspect gml-minio | grep Architecture

# Expected: "arm64"
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
docker-compose -f docker-compose.dev.yml logs service-name

# Remove and recreate
docker-compose -f docker-compose.dev.yml rm -f service-name
docker-compose -f docker-compose.dev.yml up -d service-name
```

### Health Check Failing

```bash
# Check service logs
docker-compose -f docker-compose.dev.yml logs service-name

# Manually test health check command
docker exec service-name <health-check-command>

# Increase health check timeout in docker-compose.dev.yml if needed
```

### Port Already in Use

```bash
# Find process using port
lsof -i :PORT_NUMBER

# Kill process (if safe to do so)
kill -9 PID

# Or change port mapping in docker-compose.dev.yml
```

### Volume Issues

```bash
# Remove all volumes (WARNING: Deletes data)
docker-compose -f docker-compose.dev.yml down -v

# Recreate volumes
docker-compose -f docker-compose.dev.yml up -d
```

## Complete Reset

If you need to completely reset the environment:

```bash
# Stop and remove all containers, networks, and volumes
docker-compose -f docker-compose.dev.yml down -v

# Remove orphaned containers
docker-compose -f docker-compose.dev.yml down --remove-orphans

# Clean up unused resources
docker system prune -a --volumes

# Start fresh
docker-compose -f docker-compose.dev.yml up -d
```

## Quick Reference Commands

```bash
# Status check
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs service-name

# Restart
docker-compose -f docker-compose.dev.yml down && docker-compose -f docker-compose.dev.yml up -d

# Restart specific service
docker-compose -f docker-compose.dev.yml restart service-name

# Stop all
docker-compose -f docker-compose.dev.yml down

# Start all
docker-compose -f docker-compose.dev.yml up -d
```

