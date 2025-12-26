# How GML Infrastructure Works

## System Architecture Overview

GML Infrastructure is a Graph Machine Learning platform that connects multiple AI agents through a shared memory system. This document explains how the system stores memories, connects models, and enables agents to share information.

## Memory Storage System

### 1. Database Storage (PostgreSQL)

**Location:** PostgreSQL Database - `memories` table

**Storage Details:**
- **Table:** `memories`
- **Primary Storage:** Full memory content is stored as JSON in PostgreSQL
- **Structure:**
  - `context_id`: Unique identifier (e.g., `ctx-abc-123`)
  - `agent_id`: Owner agent identifier
  - `conversation_id`: Links memories to conversations
  - `content`: JSON object containing the actual memory data
  - `memory_type`: Type classification (episodic, semantic, procedural)
  - `tags`: Array of tags for categorization
  - `visibility`: Access control (all, organization, private)
  - `created_at`: Timestamp

**Example Storage:**
```json
{
  "context_id": "ctx-abc-123",
  "agent_id": "my-agent-001",
  "content": {
    "user_message": "I prefer dark mode",
    "assistant_response": "Noted, I'll remember your preference",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "memory_type": "semantic",
  "tags": ["ui", "preference"],
  "visibility": "private"
}
```

### 2. Vector Database (Qdrant)

**Location:** Qdrant Vector Database

**Storage Details:**
- **Collection:** `memories`
- **Purpose:** Semantic search and similarity matching
- **Content:** Vector embeddings (1536 dimensions by default)
- **Indexed Fields:**
  - Vector embedding (for similarity search)
  - `agent_id` (in payload)
  - `memory_type` (in payload)
  - `context_id` (as point ID)

**How Embeddings Work:**
1. Text content is extracted from memory JSON
2. OpenAI-compatible embedding model converts text to 1536-dimensional vector
3. Vector is stored in Qdrant with metadata payload
4. Similarity search uses cosine similarity between vectors

### 3. Memory Flow Process

#### Writing a Memory:

```
User Input → Chat Interface
    ↓
Frontend sends: POST /api/v1/memory/write
    ↓
Backend Processing:
  1. Validates agent ID (from X-Agent-ID header)
  2. Generates unique context_id
  3. Extracts text from content JSON
  4. Generates embedding vector
  5. Stores in PostgreSQL (full content)
  6. Stores in Qdrant (vector + metadata)
  7. Records cost
    ↓
Response: { context_id, version }
```

#### Searching Memories:

```
User Query → Chat Interface
    ↓
Frontend sends: POST /api/v1/memory/search
    Body: { query: "user preferences", limit: 3 }
    ↓
Backend Processing:
  1. Validates agent ID
  2. Converts query to embedding vector
  3. Searches Qdrant for similar vectors
  4. Returns top-N matches with similarity scores
  5. Retrieves full content from PostgreSQL
    ↓
Response: { results: [...], total: N }
```

## Multi-Model Connection System

### Model Integration Architecture

**Current Implementation:**
- **Ollama Service:** Local LLM inference engine
- **Models:** Multiple models can be registered (gpt-oss:20b, llama2:13b, etc.)
- **API Endpoint:** `/api/v1/ollama/*`

### How Models Connect:

1. **Model Registration:**
   - Models are registered in Ollama (local service)
   - Available via: `GET /api/v1/ollama/models`
   - Each model has a unique identifier

2. **Model Selection:**
   - User selects model from dropdown in Chat interface
   - Model identifier is sent with each request
   - Default model: `gpt-oss:20b`

3. **Request Flow:**
   ```
   Chat Input → Frontend
       ↓
   Search Memories (get context)
       ↓
   Build Prompt (context + user message)
       ↓
   POST /api/v1/ollama/simple
   Query Params: { message, system_message, model }
       ↓
   Backend → Ollama Service
       ↓
   Ollama → Local LLM Model (selected model)
       ↓
   Response → Backend → Frontend
       ↓
   Save Conversation to Memory
   ```

### Model Sharing Mechanism

**Shared Resources:**
1. **Memory System:** All models can access shared memories
2. **Agent System:** Models are associated with agents
3. **Conversation Context:** Shared through memory system

**Data Flow Between Models:**
- Models don't directly communicate
- Communication happens through:
  1. **Shared Memory:** Models read/write to same memory store
  2. **Agent Association:** Models inherit agent's memory access
  3. **Conversation Threads:** Linked through conversation_id

## Agent Sharing System

### How Agents Share Data

**Shared Resources:**

1. **Memory Visibility Levels:**
   - **"all":** All agents can read
   - **"organization":** Agents in same organization
   - **"private":** Only owning agent

2. **Memory Search:**
   - All agents can search shared memories
   - Results filtered by visibility rules
   - Access control enforced by backend

3. **Agent Communication:**
   - Agents communicate via shared memory
   - No direct agent-to-agent API
   - Memory acts as message broker

**Example Flow:**
```
Agent A writes memory with visibility="all"
    ↓
Agent B searches for relevant information
    ↓
Memory search returns Agent A's memory
    ↓
Agent B uses context in its response
    ↓
Agent B writes its own memory
    ↓
Both memories now available to all agents
```

## Chat Interface Flow

### Complete Request Flow:

1. **User Types Message**
   - Input captured in Chat component

2. **Memory Search (Automatic)**
   - Query sent to `/api/v1/memory/search`
   - Top 3 relevant memories retrieved
   - Context formatted for prompt

3. **Prompt Construction**
   - Format: `[Memory context]\n\nUser: [message]`
   - System message: Agent identity prompt

4. **Model Request**
   - POST to `/api/v1/ollama/simple`
   - Includes: message, system_message, model

5. **Backend Processing**
   - Ollama service processes request
   - Local LLM generates response
   - Response streamed back

6. **Response Display**
   - Markdown rendering
   - Live typing animation
   - Formatted output (no hashtags)

7. **Memory Save (Automatic)**
   - Conversation saved to memory
   - Stored in PostgreSQL
   - Embedding generated and stored in Qdrant

## Data Persistence

### What Gets Stored Where:

**PostgreSQL (Relational Data):**
- Full memory content (JSON)
- Agent records
- Message logs
- Cost records
- Audit logs

**Qdrant (Vector Data):**
- Memory embeddings (vectors)
- Searchable metadata
- Similarity index

**Redis (Cache/Session):**
- Message queues
- Pub/Sub channels
- Session data

## Security & Access Control

### Agent Authentication:
- **Header:** `X-Agent-ID: {agent_id}`
- **Validation:** Backend verifies agent exists
- **Access:** Agent can only access allowed memories

### Memory Access Rules:
- Owner always has access
- Visibility rules enforced
- Organization boundaries respected
- Private memories isolated

## Performance Optimization

### Caching Strategy:
- Frequently accessed memories cached
- Embeddings pre-computed
- Search results cached

### Query Optimization:
- Vector search optimized with indexes
- Database queries use indexes
- Pagination for large result sets

## Future Enhancements

1. **Streaming Responses:**
   - Real-time token streaming
   - Progressive rendering

2. **Multi-Agent Coordination:**
   - Direct agent-to-agent messaging
   - Agent orchestration

3. **Advanced Memory Types:**
   - Hierarchical memories
   - Memory relationships
   - Temporal memory links

