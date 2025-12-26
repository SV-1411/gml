# GML Infrastructure - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Features](#features)
5. [System Components](#system-components)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Frontend Pages](#frontend-pages)
9. [Setup & Installation](#setup--installation)
10. [How It Works](#how-it-works)
11. [Services Integration](#services-integration)
12. [Future Enhancements](#future-enhancements)

---

## Project Overview

**GML (General Machine Learning) Infrastructure** is a comprehensive AI agent management system that provides:
- **Multi-agent orchestration** with individual memory systems
- **Semantic memory search** using vector embeddings
- **File storage** for documents and media
- **Real-time chat interface** with multiple AI models
- **Complete dashboard** for monitoring and management

The system enables multiple AI agents to work independently while sharing knowledge through a centralized memory system with semantic search capabilities.

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React + TypeScript)          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Dashboard │ │   Chat   │ │  Agents  │ │ Memories │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│              Backend (FastAPI + Python)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Agents  │ │ Memories │ │  Health  │ │ Storage  │      │
│  │  API     │ │   API    │ │   API    │ │   API    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└──────┬──────────┬──────────┬──────────┬──────────┬─────────┘
       │          │          │          │          │
┌──────▼──────┐ ┌─▼──────┐ ┌─▼──────┐ ┌─▼──────┐ ┌─▼──────┐
│ PostgreSQL  │ │ Redis  │ │ Qdrant │ │ MinIO  │ │ Ollama │
│  (Primary   │ │ (Cache)│ │(Vector │ │(Object │ │  (LLM) │
│  Database)  │ │        │ │Search) │ │Storage)│ │        │
└─────────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### Data Flow

1. **Agent Registration**: User registers agents → Stored in PostgreSQL
2. **Memory Creation**: Agents create memories → Content stored in PostgreSQL, embeddings in Qdrant
3. **File Upload**: Files uploaded → Stored in MinIO, URLs saved in memory content
4. **Semantic Search**: Query → Embedded → Searched in Qdrant → Relevant memories returned
5. **Chat**: User message → Memory search → Context sent to Ollama → Response streamed

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.13)
- **Database**: PostgreSQL (primary data storage)
- **Cache**: Redis (session/caching layer)
- **Vector Database**: Qdrant (semantic search embeddings)
- **Object Storage**: MinIO (S3-compatible file storage)
- **LLM Server**: Ollama (local AI models)
- **ORM**: SQLAlchemy (async)
- **Validation**: Pydantic
- **Monitoring**: Prometheus metrics

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Markdown**: react-markdown (for AI responses)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: Alembic
- **Environment**: Python virtual environment

---

## Features

### 1. **Agent Management**
- ✅ Register new AI agents with unique IDs and API tokens
- ✅ View all registered agents
- ✅ Activate/Deactivate agents
- ✅ Agent status tracking (active/inactive)
- ✅ Agent authentication via API tokens

### 2. **Memory System**
- ✅ Create memories with multiple types:
  - **Episodic**: Event-based memories (what happened when)
  - **Semantic**: Fact-based memories (what is known)
  - **Procedural**: Skill-based memories (how to do things)
- ✅ Memory content stored as JSON
- ✅ Support for text and file uploads
- ✅ File storage in MinIO with URLs
- ✅ Semantic search using vector embeddings
- ✅ Memory visibility levels (all, organization, private)

### 3. **Semantic Search**
- ✅ Vector-based semantic search using Qdrant
- ✅ Query embeddings generated automatically
- ✅ Relevance scoring and ranking
- ✅ Filtering by memory type and conversation ID
- ✅ Search limit: up to 100 results per query

### 4. **File Storage**
- ✅ File upload via API
- ✅ Multiple file types supported (PDF, images, documents)
- ✅ S3-compatible MinIO storage
- ✅ Storage URLs for file access
- ✅ File metadata (size, type) tracking

### 5. **Chat Interface**
- ✅ ChatGPT-like chat UI
- ✅ Multiple AI model support (Ollama models)
- ✅ Real-time streaming responses
- ✅ Live "thinking" animations
- ✅ Memory context integration
- ✅ Markdown rendering for responses
- ✅ Conversation history

### 6. **Dashboard**
- ✅ Real-time statistics:
  - Total agents (with active/inactive breakdown)
  - Total memories (with type breakdown)
  - Files in storage (with total size)
  - System health status
- ✅ System health monitoring:
  - Database connectivity
  - Redis status
  - Qdrant status
  - MinIO status
- ✅ Agents list (all registered agents)
- ✅ Recent memories display
- ✅ Auto-refresh every 30 seconds

### 7. **System Monitoring**
- ✅ Health check endpoints
- ✅ Detailed service health status
- ✅ Prometheus metrics integration
- ✅ Error tracking and logging

---

## System Components

### Backend Components

#### 1. **API Layer** (`src/gml/api/`)
- **Main Application**: FastAPI app with middleware, CORS, error handling
- **Routes**:
  - `agents.py`: Agent registration, retrieval, status management
  - `memory.py`: Memory CRUD, semantic search
  - `health.py`: Health checks and metrics
  - `storage.py`: File upload/download
  - `ollama.py`: LLM model integration

#### 2. **Database Layer** (`src/gml/db/`)
- **Models**: SQLAlchemy models for agents, memories, conversations
- **Database**: PostgreSQL connection and session management
- **Migrations**: Alembic for schema versioning

#### 3. **Services** (`src/gml/services/`)
- **AgentService**: Agent business logic
- **MessageService**: Message handling
- **EmbeddingService**: Vector embedding generation
- **OllamaService**: LLM API integration
- **CostService**: Token usage tracking
- **MinIOService**: File storage operations

#### 4. **Core** (`src/gml/core/`)
- **Config**: Environment configuration management
- **Security**: API key validation, authentication
- **Constants**: System-wide constants

#### 5. **Monitoring** (`src/gml/monitoring/`)
- **Metrics**: Prometheus metrics collection

### Frontend Components

#### 1. **Pages**
- **Dashboard**: Main overview with stats and recent activity
- **Chat**: AI chat interface with streaming
- **Agents**: Agent management and registration
- **Memories**: Memory search and creation
- **Settings**: Configuration and agent selection

#### 2. **Components**
- **Layout**: Sidebar navigation and header
- **MemoryForm**: Memory creation form (text/JSON/file upload)
- **AgentForm**: Agent registration form

#### 3. **Services**
- **API**: Centralized API client with interceptors

#### 4. **Contexts**
- **Theme**: Light/dark mode management

---

## Database Schema

### Agents Table
```sql
- id: UUID (Primary Key)
- name: String
- api_token: String (hashed)
- status: Enum (active/inactive)
- created_at: Timestamp
- updated_at: Timestamp
```

### Memories Table
```sql
- context_id: UUID (Primary Key)
- agent_id: UUID (Foreign Key → Agents)
- conversation_id: String
- content: JSONB (memory content)
- memory_type: Enum (episodic/semantic/procedural)
- visibility: Enum (all/organization/private)
- tags: Array[String]
- created_at: Timestamp
- created_by: String
```

### Conversations Table
```sql
- conversation_id: String (Primary Key)
- agent_id: UUID (Foreign Key → Agents)
- created_at: Timestamp
- updated_at: Timestamp
```

### Vector Embeddings
- Stored in **Qdrant** collection
- 1536-dimensional vectors (default)
- Linked to memory `context_id`

---

## API Endpoints

### Agents API (`/api/v1/agents`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new agent |
| GET | `/` | Get all agents (with pagination) |
| GET | `/{agent_id}` | Get agent by ID |
| PATCH | `/{agent_id}/status` | Update agent status (active/inactive) |

### Memory API (`/api/v1/memory`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/write` | Create a new memory |
| GET | `/{context_id}` | Get memory by context ID |
| POST | `/search` | Semantic search memories |

**Search Parameters:**
- `query`: Search text (required)
- `memory_type`: Filter by type (optional)
- `conversation_id`: Filter by conversation (optional)
- `limit`: Max results (1-100, default: 10)

### Storage API (`/api/v1/storage`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a file |
| GET | `/url/{key}` | Get file URL |

### Health API (`/api/v1/health`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Basic health check |
| GET | `/detailed` | Detailed service health status |

### Ollama API (`/api/v1/ollama`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models` | List available models |
| POST | `/chat` | Chat with AI model (streaming) |

---

## Frontend Pages

### 1. Dashboard (`/dashboard`)
**Purpose**: Main overview and monitoring

**Features**:
- Statistics cards (agents, memories, files, health)
- System health status for all services
- List of all registered agents
- Recent memories with file information
- Auto-refresh every 30 seconds
- Manual refresh button

**Data Displayed**:
- Total agents (active/inactive breakdown)
- Total memories (with type breakdown)
- Files in storage (count and total size)
- System health (individual service status)
- All agents list with status badges
- 10 most recent memories

### 2. Chat (`/chat`)
**Purpose**: Interactive AI chat interface

**Features**:
- ChatGPT-like UI
- Model selection dropdown
- Message history
- Streaming responses
- Live thinking animations
- Memory context integration
- Markdown rendering
- Auto-scroll to latest message

**Functionality**:
- User sends message → System searches memories → Context + message sent to Ollama → Response streamed back

### 3. Agents (`/agents`)
**Purpose**: Agent management

**Features**:
- List all registered agents
- Register new agent form
- Agent details (ID, name, status, created date)
- Activate/Deactivate toggle
- Status badges

**Agent Registration**:
- Name (required)
- Auto-generated ID and API token
- Default status: inactive

### 4. Memories (`/memories`)
**Purpose**: Memory search and creation

**Features**:
- Memory search with semantic search
- Memory statistics (total, with files, storage size, coverage)
- Create memory form:
  - Text or JSON input
  - File upload (optional)
  - Memory type selection
  - Visibility setting
  - Tags
- Display all memories by default
- Memory cards showing:
  - Memory ID
  - Type badge
  - Content preview
  - Storage URLs (if file uploaded)
  - Creation date

### 5. Settings (`/settings`)
**Purpose**: Configuration management

**Features**:
- Select default agent ID
- View registered agents
- Set agent ID from dropdown or manual input
- Agent ID stored in localStorage for API requests

---

## Setup & Installation

### Prerequisites
- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- Git

### Backend Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd project
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start Docker Services**
   ```bash
   docker-compose up -d
   ```
   This starts:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - Qdrant (ports 6333, 6334)
   - MinIO (ports 9000, 9001)

6. **Run Database Migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start Backend Server**
   ```bash
   cd src
   uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to Frontend Directory**
   ```bash
   cd frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```
   Frontend runs on `http://localhost:3000`

### Verify Installation

1. **Backend**: `http://localhost:8000/api/docs` (Swagger UI)
2. **Frontend**: `http://localhost:3000`
3. **MinIO Console**: `http://localhost:9001` (default: minioadmin/minioadmin)
4. **Qdrant Dashboard**: `http://localhost:6333/dashboard`

---

## How It Works

### 1. Agent Registration Flow

```
User → Frontend → POST /api/v1/agents/register
  ↓
Backend validates request
  ↓
Generate unique agent ID and API token
  ↓
Hash API token
  ↓
Store in PostgreSQL
  ↓
Return agent details to frontend
  ↓
Display agent ID and token (shown once)
```

### 2. Memory Creation Flow

```
User creates memory with content/file
  ↓
Frontend → POST /api/v1/memory/write
  ↓
Backend validates request
  ↓
If file uploaded:
  - Upload to MinIO
  - Get storage URL
  - Add URL to memory content
  ↓
Store memory in PostgreSQL
  ↓
Generate embedding from content
  ↓
Store embedding in Qdrant (linked to context_id)
  ↓
Return memory details
```

### 3. Semantic Search Flow

```
User enters search query
  ↓
Frontend → POST /api/v1/memory/search
  ↓
Backend generates embedding from query
  ↓
Search Qdrant for similar vectors
  ↓
Retrieve matching memory IDs
  ↓
Fetch memory details from PostgreSQL
  ↓
Calculate similarity scores
  ↓
Return ranked results
```

### 4. Chat Flow

```
User sends message
  ↓
Frontend searches memories for context
  ↓
Retrieve relevant memories from Qdrant + PostgreSQL
  ↓
Frontend → POST /api/v1/ollama/chat
  ↓
Backend sends message + context to Ollama
  ↓
Ollama generates response (streaming)
  ↓
Backend streams response back to frontend
  ↓
Frontend displays streaming text
```

### 5. File Upload Flow

```
User selects file in memory form
  ↓
Frontend uploads file → POST /api/v1/storage/upload
  ↓
Backend receives multipart/form-data
  ↓
Generate unique filename
  ↓
Upload to MinIO bucket
  ↓
Generate storage URL
  ↓
Return URL to frontend
  ↓
URL stored in memory content
```

---

## Services Integration

### PostgreSQL
- **Purpose**: Primary relational database
- **Stores**: Agents, memories, conversations
- **Connection**: Async SQLAlchemy
- **Port**: 5432

### Redis
- **Purpose**: Caching and session management
- **Connection**: Redis async client
- **Port**: 6379

### Qdrant
- **Purpose**: Vector similarity search
- **Stores**: Memory embeddings (1536 dimensions)
- **Collection**: Linked to memory context_ids
- **Port**: 6333 (HTTP), 6334 (gRPC)

### MinIO
- **Purpose**: S3-compatible object storage
- **Stores**: Uploaded files (PDFs, images, documents)
- **Buckets**: `uploads` (auto-created)
- **Ports**: 9000 (API), 9001 (Console)
- **Default Credentials**: minioadmin/minioadmin

### Ollama
- **Purpose**: Local LLM inference server
- **Models**: Various (gpt-oss:20b, llama2, etc.)
- **API**: OpenAI-compatible API
- **Port**: 11434 (default)

---

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gml_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uploads
MINIO_USE_SSL=false

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=gpt-oss:20b

# Security
SECRET_KEY=your-secret-key-here
API_KEY_HEADER=X-Agent-ID

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## API Authentication

All API requests (except health checks) require:
- **Header**: `X-Agent-ID: <agent_id>`
- **Header**: `X-API-Token: <api_token>` (optional for some endpoints)

The frontend automatically includes `X-Agent-ID` from localStorage.

---

## Memory Types Explained

### Episodic Memory
- **Purpose**: Store events and experiences
- **Example**: "User logged in at 2:30 PM on Jan 15, 2024"
- **Use Case**: Track user behavior and events

### Semantic Memory
- **Purpose**: Store facts and knowledge
- **Example**: "User prefers dark mode interface"
- **Use Case**: Store user preferences and facts

### Procedural Memory
- **Purpose**: Store procedures and how-to information
- **Example**: "How to reset password: 1. Go to settings... 2. Click..."
- **Use Case**: Store step-by-step instructions

---

## File Storage Details

### Supported File Types
- PDF documents
- Images (JPG, PNG, etc.)
- Text files
- Other binary files

### Storage Structure
```
MinIO Bucket: uploads/
  └── {unique_id}-{filename}
```

### File URLs
- Format: `http://localhost:9000/uploads/{file_key}`
- Publicly accessible if MinIO bucket is public
- URLs stored in memory content JSON

---

## Error Handling

### Backend
- Structured error responses with status codes
- Validation errors with detailed messages
- Database errors logged and returned as 500
- Service unavailable errors (503) for external services

### Frontend
- Error messages displayed to users
- Retry mechanisms for failed requests
- Fallback UI for loading/error states
- Console logging for debugging

---

## Security Considerations

### Current Implementation
- ✅ API token hashing (bcrypt)
- ✅ Agent ID validation
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy)
- ✅ CORS configuration

### Recommended Enhancements
- JWT tokens for sessions
- Rate limiting
- HTTPS in production
- API key rotation
- Audit logging

---

## Performance Optimizations

### Backend
- Async/await for I/O operations
- Connection pooling (PostgreSQL, Redis)
- Vector search indexing (Qdrant)
- Response caching (where appropriate)

### Frontend
- React component optimization
- Auto-refresh intervals (30s)
- Lazy loading (future enhancement)
- Request debouncing

---

## Testing

### Manual Testing
- Swagger UI: `http://localhost:8000/api/docs`
- Frontend: All pages manually tested
- API endpoints: Verified via frontend and Postman

### Automated Testing (Future)
- Unit tests for services
- Integration tests for API endpoints
- E2E tests for frontend flows

---

## Monitoring & Logging

### Health Checks
- Basic: `/api/v1/health` - Overall system status
- Detailed: `/api/v1/health/detailed` - Individual service status

### Metrics (Prometheus)
- HTTP request counts
- Error rates
- Response times
- Service availability

### Logging
- Structured logging (Python logging)
- Console output in development
- File logging (future: production)

---

## Deployment Considerations

### Production Checklist
- [ ] Change default credentials
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Set up monitoring/alerts
- [ ] Enable rate limiting
- [ ] Use environment-specific configs
- [ ] Set up CI/CD pipeline

---

## Known Limitations

1. **Memory Search Limit**: Maximum 100 results per query
2. **File Size**: No explicit limit, but MinIO default applies
3. **Concurrent Requests**: Limited by server resources
4. **Model Availability**: Depends on Ollama installation
5. **No Pagination**: Some lists show all items (consider pagination for scale)

---

## Future Enhancements

### Short Term
- [ ] Pagination for large lists
- [ ] File size limits and validation
- [ ] Export memories (JSON/CSV)
- [ ] Memory editing/deletion
- [ ] Conversation management UI

### Medium Term
- [ ] Multi-user support with authentication
- [ ] Role-based access control
- [ ] Advanced analytics and insights
- [ ] Memory versioning
- [ ] Batch file uploads

### Long Term
- [ ] Multi-tenant architecture
- [ ] GraphQL API
- [ ] Real-time collaboration
- [ ] Mobile app
- [ ] Plugin system for extensions

---

## Troubleshooting

### Common Issues

**Backend not starting:**
- Check if port 8000 is available
- Verify Docker services are running
- Check environment variables

**File upload failing:**
- Verify MinIO is running
- Check bucket exists
- Verify credentials

**Memory search not working:**
- Check Qdrant is running
- Verify embeddings are being generated
- Check memory has valid content

**Chat not responding:**
- Verify Ollama is running
- Check model is available
- Verify API endpoint

---

## Support & Resources

- **API Documentation**: `http://localhost:8000/api/docs`
- **Database Schema**: See `src/gml/db/models.py`
- **Environment Setup**: See `ENV_SETUP.md`
- **Quick Start**: See `QUICK_START.md`

---

## Version History

- **v1.0.0** (Current)
  - Initial release
  - Agent management
  - Memory system with semantic search
  - File storage integration
  - Chat interface
  - Dashboard with real-time stats

---

## Conclusion

The GML Infrastructure is a complete AI agent management platform that enables:
- ✅ Multi-agent orchestration
- ✅ Persistent memory with semantic search
- ✅ File storage and management
- ✅ Real-time AI chat
- ✅ Comprehensive monitoring and management

The system is production-ready for single-user deployments and can be extended for multi-user scenarios.

---

**Document Generated**: December 2024
**Last Updated**: December 2024

