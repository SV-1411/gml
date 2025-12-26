# 🧠 Shared Memory System - Complete Explanation

## 📋 Overview

The **Shared Memory System** in GML Infrastructure allows agents to store, retrieve, and search memories (context, knowledge, conversations) that can be shared across multiple agents or kept private. This enables agents to learn from past interactions and share knowledge with each other.

---

## 🎯 What is Shared Memory?

Shared Memory is a knowledge storage system where:
- **Agents can store** their experiences, conversations, and learned information
- **Memories can be shared** between agents (based on visibility rules)
- **Semantic search** allows finding relevant memories by meaning, not just keywords
- **Versioning** tracks changes to memories over time
- **Access control** determines who can read which memories

---

## 🗄️ Database Model

### Memory Table Structure

```python
class Memory(Base):
    __tablename__ = "memories"
    
    # Primary identifiers
    id: int                    # Auto-incrementing primary key
    context_id: str            # Unique identifier (e.g., "ctx-abc123")
    agent_id: str              # Owner agent ID
    conversation_id: str       # Conversation this memory belongs to
    
    # Content
    content: dict              # JSON content (flexible structure)
    memory_type: str           # Type: episodic, semantic, procedural
    tags: list[str]            # JSON array of tags for categorization
    
    # Access Control
    visibility: str            # "all", "organization", "private"
    readable_by: list[str]     # JSON array of agent IDs that can read
    
    # Versioning
    version: int                # Version number
    previous_version_id: int   # Link to previous version
    
    # Timestamps
    created_at: datetime       # When memory was created
    expires_at: datetime       # Optional expiration
```

### Memory Types

1. **Episodic** - Specific events, conversations, experiences
   - Example: "User asked about weather in NYC on 2025-12-20"
   
2. **Semantic** - General knowledge, facts, concepts
   - Example: "User prefers dark mode UI"
   
3. **Procedural** - How-to knowledge, processes
   - Example: "Steps to process weather data"

### Visibility Levels

1. **"all"** - All agents can read this memory
2. **"organization"** - Only agents in same organization
3. **"private"** - Only the owning agent
4. **readable_by list** - Only specific agent IDs listed

---

## 🔄 Complete Flow

### Flow 1: Writing Memory

```
┌─────────────┐
│   Agent A   │
│ (writes)    │
└──────┬──────┘
       │
       │ 1. POST /api/v1/memory/write
       │    {
       │      "conversation_id": "conv-001",
       │      "content": {"text": "User likes coffee"},
       │      "memory_type": "episodic",
       │      "visibility": "all",
       │      "tags": ["preference", "user"]
       │    }
       │
       ▼
┌─────────────────────┐
│   Memory API Route   │
│  (write_memory)     │
└──────┬──────────────┘
       │
       │ 2. Generate embedding (optional)
       │    - Extract text from content
       │    - Call EmbeddingService
       │    - Get 1536-dim vector
       │
       ▼
┌─────────────────────┐
│  Embedding Service   │
│  (OpenAI/Ollama)    │
└──────┬──────────────┘
       │
       │ 3. Return embedding vector
       │
       ▼
┌─────────────────────┐
│   Memory Service     │
│  (or direct DB)      │
└──────┬──────────────┘
       │
       │ 4. Create Memory record
       │    - Generate context_id (UUID)
       │    - Set version = 1
       │    - Store content + embedding
       │    - Apply visibility rules
       │
       ▼
┌─────────────────────┐
│   PostgreSQL DB      │
│   (memories table)   │
└─────────────────────┘
       │
       │ 5. Return context_id
       │
       ▼
┌─────────────┐
│   Agent A   │
│ (receives)  │
│ context_id  │
└─────────────┘
```

**Steps:**
1. Agent sends memory write request via API
2. API extracts text content
3. Generate embedding vector (1536 dimensions)
4. Store in database with metadata
5. Return `context_id` for future reference

---

### Flow 2: Reading Memory

```
┌─────────────┐
│   Agent B   │
│ (reads)     │
└──────┬──────┘
       │
       │ 1. GET /api/v1/memory/{context_id}
       │
       ▼
┌─────────────────────┐
│   Memory API Route   │
│  (get_memory)        │
└──────┬──────────────┘
       │
       │ 2. Check access control
       │    - Is agent_id owner? → Allow
       │    - Is visibility "all"? → Allow
       │    - Is visibility "organization"? → Check org
       │    - Is agent_id in readable_by? → Allow
       │    - Otherwise → Deny
       │
       ▼
┌─────────────────────┐
│  Access Control      │
│  (check_memory_access)│
└──────┬──────────────┘
       │
       │ 3. Query database
       │    SELECT * FROM memories
       │    WHERE context_id = ?
       │
       ▼
┌─────────────────────┐
│   PostgreSQL DB      │
│   (memories table)   │
└──────┬──────────────┘
       │
       │ 4. Return memory content
       │
       ▼
┌─────────────┐
│   Agent B   │
│ (receives)  │
│   content   │
└─────────────┘
```

**Steps:**
1. Agent requests memory by `context_id`
2. API checks access control rules
3. Query database if access granted
4. Return memory content

---

### Flow 3: Semantic Search

```
┌─────────────┐
│   Agent C   │
│ (searches)  │
└──────┬──────┘
       │
       │ 1. POST /api/v1/memory/search
       │    {
       │      "query": "user preferences",
       │      "memory_type": "episodic",
       │      "limit": 10
       │    }
       │
       ▼
┌─────────────────────┐
│   Memory API Route   │
│  (search_memories)   │
└──────┬──────────────┘
       │
       │ 2. Generate query embedding
       │    - Extract text from query
       │    - Call EmbeddingService
       │    - Get 1536-dim vector
       │
       ▼
┌─────────────────────┐
│  Embedding Service   │
│  (OpenAI/Ollama)    │
└──────┬──────────────┘
       │
       │ 3. Return query embedding
       │
       ▼
┌─────────────────────┐
│   Semantic Search    │
│  (Vector Similarity) │
└──────┬──────────────┘
       │
       │ 4. Calculate cosine similarity
       │    - Compare query vector with stored embeddings
       │    - Filter by memory_type if specified
       │    - Filter by conversation_id if specified
       │    - Apply access control
       │    - Sort by similarity score
       │    - Return top N results
       │
       ▼
┌─────────────────────┐
│   Qdrant/Vector DB   │
│   (or PostgreSQL)    │
└──────┬──────────────┘
       │
       │ 5. Return search results
       │    [
       │      {
       │        "context_id": "ctx-001",
       │        "content": {...},
       │        "similarity_score": 0.85,
       │        "created_by": "agent-a"
       │      },
       │      ...
       │    ]
       │
       ▼
┌─────────────┐
│   Agent C   │
│ (receives)  │
│   results   │
└─────────────┘
```

**Steps:**
1. Agent sends search query
2. Generate embedding for query text
3. Search vector database (Qdrant) for similar embeddings
4. Calculate similarity scores (cosine similarity)
5. Filter by access control and return top results

---

## 🔐 Access Control Flow

### Access Control Decision Tree

```
                    ┌─────────────────┐
                    │  Memory Request │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Is requester    │
                    │ the owner?      │
                    └──┬──────────┬───┘
                       │          │
                    YES│          │NO
                       │          │
                       ▼          ▼
              ┌─────────────┐  ┌─────────────────┐
              │   ALLOW     │  │ Check visibility│
              └─────────────┘  └────────┬────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │ visibility = │    │ visibility = │    │ visibility = │
            │   "all"      │    │"organization"│    │  "private"   │
            └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
                   │                  │                   │
                ALLOW              Check org          DENY
                                      │
                              ┌───────┴───────┐
                              │               │
                           Same org?      Different org?
                              │               │
                           ALLOW          DENY
```

### Access Control Rules

1. **Owner Always Has Access**
   - If `memory.agent_id == requester.agent_id` → ✅ Allow

2. **Visibility: "all"**
   - Any agent can read → ✅ Allow

3. **Visibility: "organization"**
   - Check if requester is in same organization as owner
   - Same org → ✅ Allow
   - Different org → ❌ Deny

4. **Visibility: "private"**
   - Only owner can read → ❌ Deny (unless owner)

5. **readable_by List**
   - If requester `agent_id` is in `readable_by` list → ✅ Allow
   - Otherwise → ❌ Deny

---

## 📝 API Endpoints

### 1. Write Memory

**Endpoint**: `POST /api/v1/memory/write`

**Request**:
```json
{
  "conversation_id": "conv-weather-001",
  "content": {
    "user_query": "What's the weather?",
    "response": "Sunny, 72°F",
    "timestamp": "2025-12-20T10:00:00Z"
  },
  "memory_type": "episodic",
  "visibility": "all",
  "tags": ["weather", "forecast", "user-interaction"]
}
```

**Response**:
```json
{
  "context_id": "ctx-abc123def456",
  "version": 1,
  "embedding_dimensions": 1536
}
```

**Flow**:
1. Extract text from `content`
2. Generate embedding (1536-dim vector)
3. Store in database
4. Return `context_id`

---

### 2. Get Memory

**Endpoint**: `GET /api/v1/memory/{context_id}`

**Request**: 
- Header: `X-Agent-ID: agent-123`
- Path: `/api/v1/memory/ctx-abc123def456`

**Response**:
```json
{
  "context_id": "ctx-abc123def456",
  "agent_id": "weather-agent",
  "conversation_id": "conv-weather-001",
  "content": {
    "user_query": "What's the weather?",
    "response": "Sunny, 72°F"
  },
  "memory_type": "episodic",
  "tags": ["weather", "forecast"],
  "visibility": "all",
  "version": 1,
  "created_at": "2025-12-20T10:00:00Z"
}
```

**Flow**:
1. Check access control
2. Query database
3. Return memory if access granted

---

### 3. Search Memories

**Endpoint**: `POST /api/v1/memory/search`

**Request**:
```json
{
  "query": "weather forecast",
  "memory_type": "episodic",
  "conversation_id": "conv-weather-001",
  "limit": 10
}
```

**Response**:
```json
{
  "results": [
    {
      "context_id": "ctx-abc123",
      "content": {
        "user_query": "What's the weather?",
        "response": "Sunny, 72°F"
      },
      "similarity_score": 0.89,
      "created_by": "weather-agent",
      "created_at": "2025-12-20T10:00:00Z"
    },
    {
      "context_id": "ctx-def456",
      "content": {...},
      "similarity_score": 0.75,
      ...
    }
  ],
  "total": 2,
  "query": "weather forecast"
}
```

**Flow**:
1. Generate query embedding
2. Search vector database
3. Calculate similarity scores
4. Filter by access control
5. Return top N results

---

## 🔍 Semantic Search Details

### How Semantic Search Works

1. **Text to Vector**
   ```
   Query: "user preferences"
   ↓
   Embedding Service
   ↓
   Vector: [0.123, -0.456, 0.789, ..., 0.234] (1536 dimensions)
   ```

2. **Vector Similarity**
   ```
   Query Vector: [0.123, -0.456, ...]
   Memory Vector: [0.125, -0.450, ...]
   ↓
   Cosine Similarity = 0.89
   ```

3. **Ranking**
   - Higher similarity = More relevant
   - Sort by similarity (descending)
   - Return top N results

### Embedding Generation

**Current Implementation**:
- Uses OpenAI `text-embedding-3-small` model
- Generates 1536-dimensional vectors
- Cached in Redis to avoid re-embedding

**Future Enhancement**:
- Can use Ollama models for embeddings
- Can use local embedding models
- Batch processing for efficiency

---

## 💡 Use Cases

### Use Case 1: Agent Learning from History

```
Agent A: "User asked about weather in NYC"
         ↓
    Store in Memory
         ↓
Agent B: "What did user ask about?"
         ↓
    Search Memories
         ↓
    Find: "User asked about weather in NYC"
```

### Use Case 2: Shared Knowledge Base

```
Agent A: Stores "User prefers dark mode"
         (visibility: "all")
         ↓
Agent B: Searches "user preferences"
         ↓
    Finds: "User prefers dark mode"
         ↓
Agent B: Uses this knowledge in response
```

### Use Case 3: Conversation Context

```
Conversation Flow:
1. User: "What's the weather?"
   → Agent stores: "User asked about weather"
   
2. User: "What about tomorrow?"
   → Agent searches: "weather" + conversation_id
   → Finds: "User asked about weather"
   → Agent understands: "User wants tomorrow's weather"
```

---

## 🔄 Complete Example Flow

### Scenario: Weather Agent Stores and Shares Memory

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Weather Agent Writes Memory                        │
└─────────────────────────────────────────────────────────────┘

Weather Agent → POST /api/v1/memory/write
{
  "conversation_id": "conv-001",
  "content": {
    "user_query": "Weather in NYC?",
    "response": "Sunny, 72°F",
    "location": "New York"
  },
  "memory_type": "episodic",
  "visibility": "all",
  "tags": ["weather", "nyc", "forecast"]
}

Response:
{
  "context_id": "ctx-weather-001",
  "version": 1
}

┌─────────────────────────────────────────────────────────────┐
│ Step 2: News Agent Searches for Related Information       │
└─────────────────────────────────────────────────────────────┘

News Agent → POST /api/v1/memory/search
{
  "query": "weather information",
  "limit": 5
}

Response:
{
  "results": [
    {
      "context_id": "ctx-weather-001",
      "content": {
        "user_query": "Weather in NYC?",
        "response": "Sunny, 72°F"
      },
      "similarity_score": 0.87,
      "created_by": "weather-agent"
    }
  ]
}

┌─────────────────────────────────────────────────────────────┐
│ Step 3: News Agent Uses Memory to Generate News Summary   │
└─────────────────────────────────────────────────────────────┘

News Agent:
- Found memory: "Weather in NYC: Sunny, 72°F"
- Uses this context to create news summary
- "Today's weather in NYC is sunny and warm (72°F)..."
```

---

## 🎯 Key Features

### 1. **Flexible Content Storage**
- Content stored as JSON (flexible structure)
- Can store any data format
- No schema restrictions

### 2. **Semantic Search**
- Find memories by meaning, not keywords
- Vector similarity search
- Context-aware retrieval

### 3. **Access Control**
- Fine-grained visibility rules
- Organization-level sharing
- Private memories support

### 4. **Versioning**
- Track memory changes over time
- Link to previous versions
- Maintain history

### 5. **Tagging**
- Categorize memories with tags
- Filter by tags
- Organize knowledge

### 6. **Expiration**
- Optional expiration dates
- Automatic cleanup
- Temporary memories

---

## 📊 Data Flow Diagram

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│ Agent A  │      │ Agent B  │      │ Agent C  │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │
     │ Write Memory    │ Search Memory   │ Read Memory
     │                 │                 │
     └─────────┬───────┴─────────┬───────┘
               │                 │
               ▼                 ▼
     ┌─────────────────────────────────┐
     │      Memory API Routes          │
     │  (write, get, search)           │
     └─────────┬───────────────┬───────┘
               │               │
       ┌───────┘               └───────┐
       │                               │
       ▼                               ▼
┌──────────────┐              ┌──────────────┐
│  Embedding   │              │  Access      │
│  Service     │              │  Control     │
└──────┬───────┘              └──────┬───────┘
       │                             │
       │ Generate Embedding          │ Check Permissions
       │                             │
       └─────────┬───────────────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │   PostgreSQL DB       │
     │   (memories table)    │
     └───────────┬───────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │   Qdrant Vector DB    │
     │   (embeddings)        │
     └───────────────────────┘
```

---

## 🔧 Implementation Details

### Memory Write Implementation

```python
async def write_memory(
    request: MemoryWriteRequest,
    db: AsyncSession,
    agent_id: str
) -> dict:
    # 1. Extract text from content for embedding
    text_content = extract_text(request.content)
    
    # 2. Generate embedding
    embedding = await embedding_service.generate_embedding(text_content)
    
    # 3. Create memory record
    memory = Memory(
        context_id=f"ctx-{uuid.uuid4().hex[:12]}",
        agent_id=agent_id,
        conversation_id=request.conversation_id,
        content=request.content,
        memory_type=request.memory_type,
        tags=request.tags,
        visibility=request.visibility,
        version=1
    )
    
    # 4. Store in database
    db.add(memory)
    await db.commit()
    
    # 5. Store embedding in vector DB (Qdrant)
    await qdrant_client.upsert(
        collection="memories",
        points=[{
            "id": memory.context_id,
            "vector": embedding,
            "payload": {
                "agent_id": agent_id,
                "memory_type": request.memory_type
            }
        }]
    )
    
    return {
        "context_id": memory.context_id,
        "version": memory.version
    }
```

### Memory Search Implementation

```python
async def search_memories(
    request: MemorySearchRequest,
    db: AsyncSession,
    agent_id: str
) -> dict:
    # 1. Generate query embedding
    query_embedding = await embedding_service.generate_embedding(
        request.query
    )
    
    # 2. Search vector database
    results = await qdrant_client.search(
        collection="memories",
        query_vector=query_embedding,
        limit=request.limit,
        filter={
            "memory_type": request.memory_type,  # if specified
            "agent_id": agent_id  # access control
        }
    )
    
    # 3. Get full memory records from PostgreSQL
    context_ids = [r.id for r in results]
    memories = await db.execute(
        select(Memory).where(Memory.context_id.in_(context_ids))
    )
    
    # 4. Apply access control
    accessible_memories = [
        m for m in memories
        if check_memory_access(m, agent_id)
    ]
    
    # 5. Format results
    return {
        "results": [
            {
                "context_id": m.context_id,
                "content": m.content,
                "similarity_score": r.score,
                "created_by": m.agent_id,
                "created_at": m.created_at
            }
            for m, r in zip(accessible_memories, results)
        ]
    }
```

---

## 🎯 Summary

### What Shared Memory Does

1. **Stores** agent experiences, conversations, and knowledge
2. **Shares** memories between agents (based on visibility)
3. **Searches** memories semantically (by meaning)
4. **Controls** access with fine-grained permissions
5. **Versions** memories to track changes
6. **Tags** memories for organization

### Key Benefits

- ✅ **Knowledge Sharing**: Agents learn from each other
- ✅ **Context Awareness**: Agents remember past interactions
- ✅ **Semantic Search**: Find relevant information by meaning
- ✅ **Access Control**: Privacy and security
- ✅ **Scalability**: Efficient vector-based search

### Current Status

- ✅ Database model implemented
- ✅ API endpoints working
- ✅ Access control implemented
- ✅ Embedding generation ready
- ⚠️ Vector search (Qdrant integration ready, needs full implementation)

---

**The Shared Memory system enables agents to build a collective knowledge base while maintaining privacy and access control!** 🧠✨

