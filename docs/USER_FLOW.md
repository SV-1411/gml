# User Flow: UI to Backend Integration

This document describes the complete user flow from a UI perspective, showing how users interact with the system and how each action connects to the running backend API.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Initial Setup & Agent Registration](#initial-setup--agent-registration)
3. [Agent Dashboard View](#agent-dashboard-view)
4. [Chat Interface](#chat-interface)
5. [Memory Management](#memory-management)
6. [Agent Management](#agent-management)
7. [Complete User Journey Examples](#complete-user-journey-examples)

---

## Overview

The GML Infrastructure provides a Graph Machine Learning platform where users can:
- Register and manage AI agents
- Chat with AI models (Ollama LLM)
- Store and search memories semantically
- Monitor agent health and status

**Backend API Base URL**: `http://localhost:8000`  
**API Documentation**: `http://localhost:8000/api/docs`

---

## Initial Setup & Agent Registration

### User Perspective

When a user first accesses the application, they need to register an agent to get started.

#### Step 1: Access Registration Page

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  GML Infrastructure - Agent Registration                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Agent ID: [________________]                           │
│  (e.g., data-processor-001)                             │
│                                                          │
│  Agent Name: [________________]                         │
│  (e.g., Data Processor Agent)                           │
│                                                          │
│  Version: [1.0.0]                                       │
│                                                          │
│  Description:                                            │
│  [________________________________]                     │
│  [________________________________]                     │
│                                                          │
│  Capabilities:                                           │
│  ┌─────────────────────────────────────┐               │
│  │ [file_processing]                    │               │
│  │ [data_validation]                    │               │
│  └─────────────────────────────────────┘               │
│  + Add Capability                                       │
│                                                          │
│  [Register Agent]                                       │
└─────────────────────────────────────────────────────────┘
```

#### Step 2: User Fills Form

**User Actions:**
1. Types agent ID: `my-ai-agent-001`
2. Types agent name: `My AI Assistant`
3. Sets version: `1.0.0` (default)
4. Adds description: `An AI assistant for data processing tasks`
5. Adds capabilities: `file_processing`, `data_analysis`, `chat`
6. Clicks "Register Agent"

#### Step 3: Backend API Call

**Frontend → Backend:**
```http
POST http://localhost:8000/api/v1/agents/register
Content-Type: application/json

{
  "agent_id": "my-ai-agent-001",
  "name": "My AI Assistant",
  "version": "1.0.0",
  "description": "An AI assistant for data processing tasks",
  "capabilities": ["file_processing", "data_analysis", "chat"]
}
```

**Backend Response (201 Created):**
```json
{
  "agent_id": "my-ai-agent-001",
  "api_token": "gml_live_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...\n-----END PUBLIC KEY-----\n"
}
```

#### Step 4: UI Shows Success Screen

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  ✅ Agent Registered Successfully                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Agent ID: my-ai-agent-001                              │
│                                                          │
│  ⚠️  IMPORTANT: Save your API Token now!                │
│  This token will only be shown once.                    │
│                                                          │
│  API Token:                                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │ gml_live_abc123def456ghi789jkl012mno345pqr678... │ │
│  └───────────────────────────────────────────────────┘ │
│  [Copy Token] [Download Token]                          │
│                                                          │
│  Public Key:                                             │
│  ┌───────────────────────────────────────────────────┐ │
│  │ -----BEGIN PUBLIC KEY-----                        │ │
│  │ MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...              │ │
│  │ -----END PUBLIC KEY-----                          │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  [Go to Dashboard]  [Register Another Agent]            │
└─────────────────────────────────────────────────────────┘
```

**User Actions:**
- Copies API token to secure location
- Clicks "Go to Dashboard"

---

## Agent Dashboard View

### User Perspective

After registration, the user sees the main dashboard showing their agents and system status.

#### Dashboard Screen

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  GML Infrastructure Dashboard                            │
├─────────────────────────────────────────────────────────┤
│  [Agents] [Chat] [Memories] [Settings]                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 System Status                                        │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ✅ Backend API: Healthy                            │ │
│  │ ✅ Ollama Service: Healthy                         │ │
│  │ ✅ Database: Connected                             │ │
│  │ ✅ Redis: Connected                                │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  🤖 My Agents                                            │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Agent ID: my-ai-agent-001                          │ │
│  │ Name: My AI Assistant                              │ │
│  │ Status: ● Active                                   │ │
│  │ Version: 1.0.0                                     │ │
│  │ Last Heartbeat: 2 minutes ago                      │ │
│  │ [View Details] [Chat] [Manage Memories]            │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  [+ Register New Agent]                                 │
└─────────────────────────────────────────────────────────┘
```

#### Backend API Calls on Load

**1. Health Check:**
```http
GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

**2. List Agents:**
```http
GET http://localhost:8000/api/v1/agents?skip=0&limit=10
```

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "my-ai-agent-001",
      "name": "My AI Assistant",
      "status": "active",
      "api_token": null,
      "public_key": "-----BEGIN PUBLIC KEY-----\n...",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0,
  "has_more": false
}
```

**3. Ollama Health:**
```http
GET http://localhost:8000/api/v1/ollama/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Ollama service is running",
  "base_url": "http://localhost:11434",
  "model": "gpt-oss:20b"
}
```

---

## Chat Interface

### User Perspective

The chat interface allows users to interact with AI models through their registered agent.

#### Chat Screen

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  💬 Chat with My AI Assistant                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Agent: my-ai-agent-001                            │ │
│  │ Model: [gpt-oss:20b ▼] [Auto Select]            │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │                                                   │ │
│  │  User: Hello! What can you help me with?         │ │
│  │                                                   │ │
│  │  Assistant: Hello! I'm an AI assistant for data  │ │
│  │  processing tasks. I can help you with:          │ │
│  │  - File processing and validation                │ │
│  │  - Data analysis and insights                    │ │
│  │  - Chat conversations                            │ │
│  │                                                   │ │
│  │  How can I assist you today?                     │ │
│  │                                                   │ │
│  │  User: Can you analyze this data?                │ │
│  │                                                   │ │
│  │  Assistant: [Thinking...]                        │ │
│  │                                                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Type your message...                              │ │
│  └───────────────────────────────────────────────────┘ │
│  [Send] [Clear] [Search Memories]                      │
└─────────────────────────────────────────────────────────┘
```

### Complete Chat Flow

#### Step 1: User Types Message

**User Action:** Types "What is the weather in New York?"

#### Step 2: Frontend Searches Memories (Automatic)

**Backend API Call:**
```http
POST http://localhost:8000/api/v1/memory/search
X-Agent-ID: my-ai-agent-001
Content-Type: application/json

{
  "query": "What is the weather in New York?",
  "memory_type": "semantic",
  "limit": 3
}
```

**Backend Response:**
```json
{
  "query": "What is the weather in New York?",
  "results": [
    {
      "context_id": "ctx-abc-123",
      "content": {
        "text": "User prefers Celsius temperature units",
        "preference": "celsius"
      },
      "similarity_score": 0.85,
      "created_by": "my-ai-agent-001",
      "created_at": "2024-01-14T15:30:00Z"
    },
    {
      "context_id": "ctx-def-456",
      "content": {
        "text": "User location: New York, USA",
        "location": "New York"
      },
      "similarity_score": 0.72,
      "created_by": "my-ai-agent-001",
      "created_at": "2024-01-13T10:20:00Z"
    }
  ],
  "total": 2
}
```

**Frontend Processing:**
- Combines memory context with user message
- Creates enhanced prompt:
```
Relevant context from shared memory:
[Memory (similarity: 85%): User prefers Celsius temperature units]
[Memory (similarity: 72%): User location: New York, USA]

User: What is the weather in New York?
```

#### Step 3: Frontend Sends Chat Request

**Backend API Call:**
```http
POST http://localhost:8000/api/v1/ollama/simple?message=Relevant%20context%20from%20shared%20memory%3A%0A%5BMemory%20(similarity%3A%2085%25)%3A%20User%20prefers%20Celsius%20temperature%20units%5D%0A%5BMemory%20(similarity%3A%2072%25)%3A%20User%20location%3A%20New%20York%2C%20USA%5D%0A%0AUser%3A%20What%20is%20the%20weather%20in%20New%20York%3F&system_message=You%20are%20an%20AI%20agent%20(my-ai-agent-001)%20helping%20with%20data%20processing%20tasks.&model=gpt-oss:20b
```

**Backend Processing:**
1. Route handler receives request
2. OllamaService processes the message
3. Sends to Ollama at `http://localhost:11434/v1`
4. Ollama LLM generates response

**Backend Response:**
```json
{
  "response": "Based on your location in New York, the current weather is sunny with a temperature of 22°C (72°F). There's a light breeze from the west. Perfect weather for outdoor activities!",
  "model": "gpt-oss:20b"
}
```

#### Step 4: UI Displays Response

**UI Screen Updates:**
```
┌───────────────────────────────────────────────────┐
│                                                   │
│  User: What is the weather in New York?          │
│                                                   │
│  Assistant: Based on your location in New York,  │
│  the current weather is sunny with a temperature │
│  of 22°C (72°F). There's a light breeze from the │
│  west. Perfect weather for outdoor activities!   │
│                                                   │
│  📝 Context used: 2 memories (85%, 72%)          │
│                                                   │
└───────────────────────────────────────────────────┘
```

#### Step 5: Frontend Saves Conversation to Memory (Automatic)

**Backend API Call:**
```http
POST http://localhost:8000/api/v1/memory/write
X-Agent-ID: my-ai-agent-001
Content-Type: application/json

{
  "conversation_id": "conv-xyz-789",
  "content": {
    "user_message": "What is the weather in New York?",
    "assistant_response": "Based on your location in New York, the current weather is sunny with a temperature of 22°C (72°F)...",
    "timestamp": "2024-01-15T14:30:00Z"
  },
  "memory_type": "episodic",
  "visibility": "private",
  "tags": ["weather", "location", "conversation"]
}
```

**Backend Response (201 Created):**
```json
{
  "context_id": "ctx-new-789",
  "version": 1
}
```

**What Happens in Backend:**
1. Validates agent ID from header
2. Generates unique context_id
3. Creates vector embedding for semantic search
4. Stores memory in PostgreSQL
5. Stores embedding in vector database (Qdrant)
6. Records cost for memory write operation

---

## Memory Management

### User Perspective

Users can view, search, and manage their agent's memories.

#### Memory Search Screen

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  🧠 Memory Management - my-ai-agent-001                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Search Memories:                                        │
│  ┌───────────────────────────────────────────────────┐ │
│  │ [Search for memories...]                          │ │
│  └───────────────────────────────────────────────────┘ │
│  Type: [All ▼]  Conversation: [All ▼]                  │
│                                                          │
│  Results (2 found):                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 📝 Context: ctx-abc-123                           │ │
│  │ Type: Semantic                                    │ │
│  │ Similarity: 85%                                   │ │
│  │ Created: Jan 14, 2024 15:30                       │ │
│  │                                                   │ │
│  │ Content:                                          │ │
│  │   "User prefers Celsius temperature units"        │ │
│  │                                                   │ │
│  │ Tags: preference, ui, celsius                     │ │
│  │ [View Details] [Delete]                           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 📝 Context: ctx-def-456                           │ │
│  │ Type: Semantic                                    │ │
│  │ Similarity: 72%                                   │ │
│  │ Created: Jan 13, 2024 10:20                       │ │
│  │                                                   │ │
│  │ Content:                                          │ │
│  │   "User location: New York, USA"                  │ │
│  │                                                   │ │
│  │ Tags: location, user-info                         │ │
│  │ [View Details] [Delete]                           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  [+ Create New Memory]                                  │
└─────────────────────────────────────────────────────────┘
```

### Create Memory Flow

#### Step 1: User Clicks "Create New Memory"

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  ✏️  Create New Memory                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Conversation ID: [conv-xyz-789]                        │
│                                                          │
│  Memory Type:                                           │
│  ○ Episodic  ● Semantic  ○ Procedural                  │
│                                                          │
│  Visibility:                                            │
│  ● All  ○ Organization  ○ Private                      │
│                                                          │
│  Content (JSON):                                        │
│  ┌───────────────────────────────────────────────────┐ │
│  │ {                                                 │ │
│  │   "text": "User prefers dark mode interface",     │ │
│  │   "preference": "dark",                           │ │
│  │   "category": "ui-settings"                       │ │
│  │ }                                                 │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  Tags: [dark-mode] [ui] [preference]                    │
│                                                          │
│  [Save Memory]  [Cancel]                                │
└─────────────────────────────────────────────────────────┘
```

#### Step 2: User Fills Form and Clicks Save

**Backend API Call:**
```http
POST http://localhost:8000/api/v1/memory/write
X-Agent-ID: my-ai-agent-001
Content-Type: application/json

{
  "conversation_id": "conv-xyz-789",
  "content": {
    "text": "User prefers dark mode interface",
    "preference": "dark",
    "category": "ui-settings"
  },
  "memory_type": "semantic",
  "visibility": "all",
  "tags": ["dark-mode", "ui", "preference"]
}
```

**Backend Processing:**
1. Validates agent ID from `X-Agent-ID` header
2. Verifies agent exists in database
3. Generates unique context_id (e.g., `ctx-new-999`)
4. Generates vector embedding for semantic search
5. Stores memory in PostgreSQL database
6. Stores embedding in vector database
7. Records cost for memory write operation

**Backend Response (201 Created):**
```json
{
  "context_id": "ctx-new-999",
  "version": 1
}
```

#### Step 3: UI Shows Success

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  ✅ Memory Created Successfully                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Context ID: ctx-new-999                                │
│  Version: 1                                             │
│                                                          │
│  Your memory has been saved and is now searchable.     │
│                                                          │
│  [View Memory]  [Create Another]  [Back to List]        │
└─────────────────────────────────────────────────────────┘
```

### View Memory Details Flow

#### Step 1: User Clicks "View Details" on a Memory

**Backend API Call:**
```http
GET http://localhost:8000/api/v1/memory/ctx-abc-123
X-Agent-ID: my-ai-agent-001
```

**Backend Response:**
```json
{
  "context_id": "ctx-abc-123",
  "agent_id": "my-ai-agent-001",
  "memory_type": "semantic",
  "created_at": "2024-01-14T15:30:00Z",
  "version": 1,
  "embedding_dimensions": 1536
}
```

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  📝 Memory Details - ctx-abc-123                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Context ID: ctx-abc-123                                │
│  Agent ID: my-ai-agent-001                              │
│  Type: Semantic                                         │
│  Visibility: All                                        │
│  Version: 1                                             │
│  Created: Jan 14, 2024 15:30:00 UTC                     │
│  Embedding Dimensions: 1536                             │
│                                                          │
│  Content:                                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │ {                                                 │ │
│  │   "text": "User prefers Celsius temperature units",│ │
│  │   "preference": "celsius"                          │ │
│  │ }                                                 │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  Tags: preference, ui, celsius                          │
│                                                          │
│  [Edit]  [Delete]  [Back to List]                       │
└─────────────────────────────────────────────────────────┘
```

---

## Agent Management

### User Perspective

Users can view and manage all their registered agents.

#### Agent List Screen

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  🤖 Agent Management                                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Filters:                                                │
│  Status: [All ▼]  Organization: [All ▼]                 │
│                                                          │
│  Agents (1 total):                                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Agent ID: my-ai-agent-001                         │ │
│  │ Name: My AI Assistant                             │ │
│  │ Status: ● Active                                  │ │
│  │ Version: 1.0.0                                    │ │
│  │ Created: Jan 15, 2024 10:30                       │ │
│  │ Last Heartbeat: 2 minutes ago                     │ │
│  │                                                   │ │
│  │ Capabilities:                                      │ │
│  │ [file_processing] [data_analysis] [chat]          │ │
│  │                                                   │ │
│  │ [View Details] [Edit] [View Memories]             │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  [+ Register New Agent]                                 │
└─────────────────────────────────────────────────────────┘
```

### View Agent Details Flow

#### Step 1: User Clicks "View Details"

**Backend API Call:**
```http
GET http://localhost:8000/api/v1/agents/my-ai-agent-001
```

**Backend Response:**
```json
{
  "agent_id": "my-ai-agent-001",
  "name": "My AI Assistant",
  "status": "active",
  "api_token": null,
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...\n-----END PUBLIC KEY-----\n",
  "created_at": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "description": "An AI assistant for data processing tasks",
  "last_heartbeat": "2024-01-15T14:28:00Z",
  "capabilities": ["file_processing", "data_analysis", "chat"]
}
```

**UI Screen:**
```
┌─────────────────────────────────────────────────────────┐
│  🤖 Agent Details - my-ai-agent-001                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Agent ID: my-ai-agent-001                              │
│  Name: My AI Assistant                                  │
│  Status: ● Active                                       │
│  Version: 1.0.0                                         │
│                                                          │
│  Description:                                            │
│  An AI assistant for data processing tasks              │
│                                                          │
│  Capabilities:                                           │
│  • file_processing                                       │
│  • data_analysis                                         │
│  • chat                                                  │
│                                                          │
│  Created: Jan 15, 2024 10:30:00 UTC                     │
│  Last Heartbeat: Jan 15, 2024 14:28:00 UTC              │
│                                                          │
│  Public Key:                                             │
│  ┌───────────────────────────────────────────────────┐ │
│  │ -----BEGIN PUBLIC KEY-----                        │ │
│  │ MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...              │ │
│  │ -----END PUBLIC KEY-----                          │ │
│  └───────────────────────────────────────────────────┘ │
│                                                          │
│  [Edit Agent]  [View Memories]  [Chat]  [Back to List]  │
└─────────────────────────────────────────────────────────┘
```

---

## Complete User Journey Examples

### Journey 1: First-Time User Setup

**User Story:** Sarah wants to use the GML Infrastructure for the first time.

1. **Accesses Application**
   - Opens browser to `http://localhost:3000`
   - Sees welcome page with "Get Started" button

2. **Registers First Agent**
   - Clicks "Register Agent"
   - Fills form:
     - Agent ID: `sarah-assistant-001`
     - Name: `Sarah's AI Assistant`
     - Capabilities: `chat`, `document_processing`
   - Clicks "Register"
   - **Backend:** `POST /api/v1/agents/register`
   - Receives API token, saves it securely

3. **Explores Dashboard**
   - **Backend:** `GET /api/v1/agents`
   - Sees her agent listed as "Active"
   - **Backend:** `GET /api/v1/ollama/health`
   - Sees Ollama service is healthy

4. **Starts First Chat**
   - Opens chat interface
   - Types: "Hello, can you help me?"
   - **Backend:** `POST /api/v1/memory/search` (no results yet)
   - **Backend:** `POST /api/v1/ollama/simple`
   - Receives AI response
   - **Backend:** `POST /api/v1/memory/write` (saves conversation)

5. **Creates First Memory**
   - Clicks "Create Memory"
   - Adds: "User prefers metric units"
   - **Backend:** `POST /api/v1/memory/write`
   - Memory saved successfully

**Total API Calls:** 5 requests

---

### Journey 2: Returning User Chat Session

**User Story:** John returns to chat with his agent about a project.

1. **Opens Dashboard**
   - **Backend:** `GET /api/v1/agents`
   - Sees his agent: `john-project-manager-001`

2. **Opens Chat**
   - Selects his agent
   - **Backend:** `GET /api/v1/ollama/models`
   - Sees available models: `["gpt-oss:20b", "llama2:13b"]`

3. **Asks Question**
   - Types: "What did we discuss about the project timeline?"
   - **Backend:** `POST /api/v1/memory/search`
     - Finds 3 relevant memories about project timeline
   - **Backend:** `POST /api/v1/ollama/simple`
     - AI responds with context from memories
   - **Backend:** `POST /api/v1/memory/write`
     - Saves new conversation

4. **Follow-up Question**
   - Types: "Can you create a summary of our discussion?"
   - **Backend:** `POST /api/v1/memory/search`
     - Finds previous conversation just saved
   - **Backend:** `POST /api/v1/ollama/simple`
     - AI creates summary based on all relevant memories

**Total API Calls:** 6 requests

---

### Journey 3: Agent Management Workflow

**User Story:** Maria needs to manage multiple agents for different tasks.

1. **Views All Agents**
   - Opens "Agent Management" page
   - **Backend:** `GET /api/v1/agents?skip=0&limit=100`
   - Sees list of 5 agents

2. **Filters by Status**
   - Selects "Active" filter
   - **Backend:** `GET /api/v1/agents?status=active&skip=0&limit=100`
   - Sees 4 active agents

3. **Views Agent Details**
   - Clicks on `data-processor-002`
   - **Backend:** `GET /api/v1/agents/data-processor-002`
   - Sees full agent details, capabilities, heartbeat status

4. **Searches Agent Memories**
   - Clicks "View Memories"
   - Searches: "data processing errors"
   - **Backend:** `POST /api/v1/memory/search`
     - Header: `X-Agent-ID: data-processor-002`
     - Finds memories related to errors

5. **Creates New Memory for Agent**
   - Clicks "Create Memory"
   - Adds documentation about error handling
   - **Backend:** `POST /api/v1/memory/write`
     - Header: `X-Agent-ID: data-processor-002`
   - Memory saved for this agent

**Total API Calls:** 5 requests

---

## API Endpoint Summary

### Agent Management
- `POST /api/v1/agents/register` - Register new agent
- `GET /api/v1/agents` - List all agents (with filters)
- `GET /api/v1/agents/{agent_id}` - Get agent details

### Memory Management
- `POST /api/v1/memory/write` - Create new memory (requires `X-Agent-ID` header)
- `GET /api/v1/memory/{context_id}` - Get memory by ID (requires `X-Agent-ID` header)
- `POST /api/v1/memory/search` - Semantic search memories (requires `X-Agent-ID` header)

### Ollama/LLM
- `POST /api/v1/ollama/chat` - Full chat completion
- `POST /api/v1/ollama/simple` - Simple chat interface
- `GET /api/v1/ollama/health` - Check Ollama health
- `GET /api/v1/ollama/models` - List available models

### Health & Monitoring
- `GET /health` - Basic health check
- `GET /metrics` - Prometheus metrics
- `GET /api/v1/health/detailed` - Detailed service health

---

## Key Headers

### Authentication
- `X-Agent-ID: {agent_id}` - Required for memory operations and agent-specific actions

### Request ID (Optional)
- `X-Request-ID: {uuid}` - For request tracing and debugging

---

## Error Handling in UI

### Common Error Scenarios

#### 1. Agent Not Found (404)
**UI Display:**
```
❌ Error: Agent 'my-agent-001' not found
[Go Back] [Register New Agent]
```

#### 2. Unauthorized (401)
**UI Display:**
```
⚠️  Authentication Required
Please provide Agent ID in request headers.
[Retry] [Go to Settings]
```

#### 3. Ollama Service Unavailable (500)
**UI Display:**
```
⚠️  AI Service Unavailable
Ollama service is not responding. Please check if Ollama is running.
[Check Status] [Retry]
```

#### 4. Memory Access Denied (403)
**UI Display:**
```
🚫 Access Denied
You don't have permission to access this memory.
[Go Back]
```

---

## Real-World Flow Diagram

```
User Opens Browser
       │
       ▼
[UI: Welcome/Dashboard Screen]
       │
       ├─→ Register Agent → POST /api/v1/agents/register → [Backend: AgentService]
       │                                                         │
       │                                                         ▼
       │                                                   [Database: Store Agent]
       │                                                         │
       │                                                         ▼
       │                                                   [Response: API Token]
       │                                                         │
       ▼                                                         ▼
[UI: Agent Dashboard]
       │
       ├─→ View Agents → GET /api/v1/agents → [Backend: AgentService]
       │
       ├─→ Open Chat → GET /api/v1/ollama/models → [Backend: OllamaService]
       │
       │   User Types Message
       │       │
       │       ├─→ Search Memories → POST /api/v1/memory/search → [Backend: MemoryService]
       │       │                                                         │
       │       │                                                         ▼
       │       │                                                   [Vector DB: Semantic Search]
       │       │                                                         │
       │       │                                                         ▼
       │       │                                                   [Response: Relevant Memories]
       │       │                                                         │
       │       ▼                                                         ▼
       │   [UI: Build Prompt with Context]
       │       │
       │       ├─→ Send Chat → POST /api/v1/ollama/simple → [Backend: OllamaService]
       │       │                                                         │
       │       │                                                         ▼
       │       │                                                   [Ollama: LLM Inference]
       │       │                                                         │
       │       │                                                         ▼
       │       │                                                   [Response: AI Message]
       │       │                                                         │
       │       ▼                                                         ▼
       │   [UI: Display Response]
       │       │
       │       ├─→ Save Memory → POST /api/v1/memory/write → [Backend: MemoryService]
       │                                                         │
       │                                                         ├─→ [Database: Store Memory]
       │                                                         └─→ [Vector DB: Store Embedding]
       │
       └─→ Manage Memories → GET/POST /api/v1/memory/* → [Backend: MemoryService]
```

---

## Summary

This document outlines how users interact with the GML Infrastructure UI and how each action connects to the backend API. The system provides:

1. **Agent Registration** - Users create and manage AI agents
2. **Chat Interface** - Users chat with AI models using Ollama
3. **Memory Management** - Users store and search memories semantically
4. **Agent Management** - Users view and manage multiple agents

All interactions flow through the FastAPI backend at `http://localhost:8000`, which handles:
- Agent registration and management
- Memory storage and semantic search
- Ollama LLM integration
- Health monitoring and metrics

The UI provides a seamless experience while the backend handles all the complex operations including vector embeddings, semantic search, and AI model inference.

---

**Last Updated:** 2024  
**Backend API Version:** 0.1.0  
**Documentation:** http://localhost:8000/api/docs

