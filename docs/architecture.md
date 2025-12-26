# GML Infrastructure Architecture

## Overview

GML Infrastructure is a multi-agent orchestration platform designed for scalability, reliability, and observability.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│   API Server   │   │   API Server   │   │   API Server   │
│   (FastAPI)    │   │   (FastAPI)    │   │   (FastAPI)    │
└───────┬────────┘   └───────┬────────┘   └───────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│  Cache Layer   │   │  Message Queue │   │   Database     │
│    (Redis)     │   │  (RabbitMQ)    │   │  (Supabase)    │
└────────────────┘   └───────┬────────┘   └────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
│  Task Worker   │   │  Task Worker   │   │  Task Worker   │
│   (Celery)     │   │   (Celery)     │   │   (Celery)     │
└────────────────┘   └────────────────┘   └────────────────┘
```

## Core Components

### API Layer (src/gml/api)
- RESTful API endpoints
- WebSocket connections for real-time updates
- Request validation and authentication
- Rate limiting and throttling

### Core Layer (src/gml/core)
- Agent orchestration logic
- Task management and scheduling
- Agent lifecycle management
- Inter-agent communication

### Database Layer (src/gml/db)
- Supabase integration
- Data models and schemas
- Query optimization
- Connection pooling

### Services Layer (src/gml/services)
- Business logic implementation
- Agent service
- Task service
- Execution service

### Cache Layer (src/gml/cache)
- Redis integration
- Session management
- Query result caching
- Rate limit tracking

### Workers Layer (src/gml/workers)
- Background task processing
- Job queue management
- Task scheduling with Celery Beat
- Distributed task execution

### Monitoring Layer (src/gml/monitoring)
- Prometheus metrics collection
- OpenTelemetry tracing
- Health checks
- Performance monitoring

## Data Flow

1. Client sends request to API
2. API validates and authenticates request
3. Request routed to appropriate service
4. Service checks cache for existing data
5. If cache miss, queries database
6. For long-running tasks, job queued to RabbitMQ
7. Workers pick up and process tasks
8. Results stored in database and cached
9. Response returned to client
10. Metrics collected throughout

## Scalability

### Horizontal Scaling
- API servers: Scale based on request load
- Workers: Scale based on queue depth
- Database: Supabase handles scaling

### Vertical Scaling
- Increase container resources
- Optimize database queries
- Implement connection pooling

## High Availability

- Multiple API server instances
- Redis cluster for cache redundancy
- RabbitMQ cluster for message durability
- Database replication via Supabase
- Health checks and auto-recovery

## Security

- JWT-based authentication
- Row Level Security (RLS) in database
- API rate limiting
- Input validation and sanitization
- Encrypted connections (TLS/SSL)
- Secret management via environment variables

## Observability

### Metrics
- Request rates and latencies
- Worker queue depth
- Database query performance
- Cache hit rates
- Error rates

### Logging
- Structured logging with correlation IDs
- Log aggregation
- Error tracking
- Audit trails

### Tracing
- Distributed tracing with OpenTelemetry
- Request flow visualization
- Performance bottleneck identification

## Technology Stack

- **API Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Cache**: Redis
- **Message Queue**: RabbitMQ
- **Task Queue**: Celery
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Container Orchestration**: Kubernetes
- **Language**: Python 3.11+

## Design Principles

1. **Separation of Concerns**: Clear boundaries between layers
2. **Scalability First**: Design for horizontal scaling
3. **Fault Tolerance**: Graceful degradation and recovery
4. **Observability**: Comprehensive monitoring and logging
5. **Security by Default**: Security at every layer
6. **API First**: Well-defined API contracts
7. **Test Coverage**: Comprehensive testing strategy
