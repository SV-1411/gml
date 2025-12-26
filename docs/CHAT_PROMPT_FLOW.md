# Chat Prompt Flow in GML Infrastructure

## 📍 Complete Path of a Chat Message

This document explains exactly where your chat text goes and what path it follows through the GML Infrastructure system.

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER TYPES MESSAGE                            │
│              (ChatPage.tsx - Textarea Input)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Frontend - ChatPage.tsx                                │
│  ─────────────────────────────────────────────────────────────  │
│  • User types: "What is the weather?"                           │
│  • handleSend() is triggered                                    │
│  • Message added to local state (messages array)                │
│  • Input cleared, loading state set                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Search Shared Memory                                   │
│  ─────────────────────────────────────────────────────────────  │
│  Function: searchMemory(userMessage)                            │
│  Location: ChatPage.tsx (line 139-169)                          │
│                                                                  │
│  Process:                                                       │
│  1. Calls: apiService.searchMemory(query, {agent_id, limit:3}) │
│  2. API: POST /api/v1/memory/search                             │
│  3. Backend: Semantic search in PostgreSQL + Vector DB          │
│  4. Returns: Top 3 relevant memories with similarity scores    │
│  5. Formats: "Relevant context from shared memory: [Memory...]" │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Select AI Model                                        │
│  ─────────────────────────────────────────────────────────────  │
│  Function: selectBestModel(userMessage)                         │
│  Location: ChatPage.tsx (line 95-138)                           │
│                                                                  │
│  Process:                                                       │
│  • Auto Mode: Analyzes query complexity                         │
│    - Simple queries → Smaller models (cost-optimized)          │
│    - Complex queries → Larger models (better quality)          │
│  • Manual Mode: Uses user-selected model                        │
│  • Returns: {model, reason, cost}                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Build Full Prompt                                      │
│  ─────────────────────────────────────────────────────────────  │
│  Location: ChatPage.tsx (line 219)                              │
│                                                                  │
│  fullPrompt = memoryContext                                      │
│    ? `${memoryContext}\n\nUser: ${userMessage}`                 │
│    : userMessage                                                 │
│                                                                  │
│  Example:                                                      │
│  "Relevant context from shared memory:                          │
│   [Memory (similarity: 85%): User prefers Celsius]               │
│   [Memory (similarity: 72%): User location: New York]           │
│                                                                  │
│   User: What is the weather?"                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Frontend API Call                                      │
│  ─────────────────────────────────────────────────────────────  │
│  Function: apiService.simpleChat()                               │
│  Location: dashboard/src/services/api.ts (line 846-900)         │
│                                                                  │
│  Request:                                                       │
│  POST /api/v1/ollama/simple                                     │
│  Query Parameters:                                              │
│    • message: fullPrompt (with memory context)                  │
│    • system_message: "You are an AI agent (agent_id)..."       │
│    • model: selected model (e.g., "gpt-oss:20b")                │
│                                                                  │
│  Network:                                                       │
│  Frontend (localhost:3000) → Backend (localhost:8000)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Backend API Route                                      │
│  ─────────────────────────────────────────────────────────────  │
│  Endpoint: POST /api/v1/ollama/simple                           │
│  Location: src/gml/api/routes/ollama.py (line 169-202)         │
│                                                                  │
│  Process:                                                       │
│  1. Receives: message, system_message, model (query params)     │
│  2. Gets: OllamaService singleton                               │
│  3. Calls: service.simple_chat(user_message, system_message, model)│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: Ollama Service                                         │
│  ─────────────────────────────────────────────────────────────  │
│  Function: OllamaService.simple_chat()                          │
│  Location: src/gml/services/ollama_service.py (line 130-158)   │
│                                                                  │
│  Process:                                                       │
│  1. Builds messages array:                                     │
│     [                                                           │
│       {"role": "system", "content": system_message},            │
│       {"role": "user", "content": user_message}                │
│     ]                                                           │
│  2. Calls: self.chat_completion(messages, model)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 8: Ollama API Call                                        │
│  ─────────────────────────────────────────────────────────────  │
│  Function: OllamaService.chat_completion()                      │
│  Location: src/gml/services/ollama_service.py (line 75-128)    │
│                                                                  │
│  Process:                                                       │
│  1. Uses: AsyncOpenAI client                                    │
│  2. Base URL: http://localhost:11434/v1                         │
│  3. Calls: client.chat.completions.create(                      │
│       model="gpt-oss:20b",                                      │
│       messages=[...],                                           │
│       temperature=0.7                                          │
│     )                                                           │
│                                                                  │
│  Network:                                                       │
│  Backend (localhost:8000) → Ollama (localhost:11434)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 9: Ollama Local LLM                                       │
│  ─────────────────────────────────────────────────────────────  │
│  Service: Ollama (Local AI Model Server)                        │
│  Location: http://localhost:11434                               │
│                                                                  │
│  Process:                                                       │
│  1. Receives: Messages with system prompt + user message        │
│  2. Loads: AI Model (e.g., gpt-oss:20b)                         │
│  3. Processes: Using local GPU/CPU inference                     │
│  4. Generates: AI response text                                 │
│  5. Returns: {choices: [{message: {content: "..."}}]}           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 10: Response Path (Backward)                              │
│  ─────────────────────────────────────────────────────────────  │
│  Ollama → OllamaService → API Route → Frontend                   │
│                                                                  │
│  Response Format:                                               │
│  {                                                              │
│    "response": "The weather in New York is sunny, 72°F...",    │
│    "model": "gpt-oss:20b"                                      │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 11: Frontend - Display Response                          │
│  ─────────────────────────────────────────────────────────────  │
│  Location: ChatPage.tsx (line 231-257)                          │
│                                                                  │
│  Process:                                                       │
│  1. Parses: response.response (string)                          │
│  2. Creates: assistantMsg object                                │
│  3. Adds: To messages state array                              │
│  4. Displays: In chat UI                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 12: Save to Shared Memory                                 │
│  ─────────────────────────────────────────────────────────────  │
│  Function: saveToMemory(userMessage, responseContent)          │
│  Location: ChatPage.tsx (line 172-193)                         │
│                                                                  │
│  Process:                                                       │
│  1. Calls: writeMemory() hook                                   │
│  2. API: POST /api/v1/memory/write                              │
│  3. Backend:                                                    │
│     • Generates embedding (vector)                              │
│     • Stores in PostgreSQL (memories table)                     │
│     • Stores embedding in Vector DB (Qdrant)                    │
│  4. Future: This memory can be retrieved by semantic search    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detailed Step-by-Step Breakdown

### **Step 1: User Input (Frontend)**
- **File**: `dashboard/src/pages/ChatPage.tsx`
- **Function**: `handleSend()` (line 195)
- **What happens**:
  - User types message in textarea
  - Clicks "Send" or presses Enter
  - Message is added to local React state
  - Loading state activated

### **Step 2: Search Shared Memory**
- **File**: `dashboard/src/pages/ChatPage.tsx`
- **Function**: `searchMemory()` (line 139)
- **API Call**: `POST /api/v1/memory/search`
- **What happens**:
  - Searches for relevant past conversations
  - Uses semantic search (vector similarity)
  - Returns top 3 matching memories
  - Formats as context string

### **Step 3: Model Selection**
- **File**: `dashboard/src/pages/ChatPage.tsx`
- **Function**: `selectBestModel()` (line 95)
- **What happens**:
  - **Auto Mode**: Analyzes query complexity
    - Simple → Smaller model (cost-optimized)
    - Complex → Larger model (better quality)
  - **Manual Mode**: Uses user-selected model
  - Returns model name, reason, and estimated cost

### **Step 4: Build Prompt**
- **File**: `dashboard/src/pages/ChatPage.tsx`
- **Line**: 219
- **What happens**:
  - Combines memory context + user message
  - Creates full prompt for AI model
  - Format: `[Memory context]\n\nUser: [message]`

### **Step 5: Frontend API Call**
- **File**: `dashboard/src/services/api.ts`
- **Function**: `apiService.simpleChat()` (line 846)
- **Request**:
  ```
  POST /api/v1/ollama/simple?message=...&system_message=...&model=...
  ```
- **Network**: Frontend → Backend (localhost:8000)

### **Step 6: Backend Route Handler**
- **File**: `src/gml/api/routes/ollama.py`
- **Function**: `simple_chat()` (line 169)
- **What happens**:
  - Receives query parameters
  - Gets OllamaService instance
  - Calls service method

### **Step 7: Ollama Service**
- **File**: `src/gml/services/ollama_service.py`
- **Function**: `simple_chat()` (line 130)
- **What happens**:
  - Builds messages array with system + user messages
  - Calls `chat_completion()` method

### **Step 8: Ollama API Call**
- **File**: `src/gml/services/ollama_service.py`
- **Function**: `chat_completion()` (line 75)
- **What happens**:
  - Uses AsyncOpenAI client
  - Connects to Ollama at `http://localhost:11434/v1`
  - Sends chat completion request
  - **Network**: Backend → Ollama (localhost:11434)

### **Step 9: Ollama LLM Processing**
- **Service**: Ollama (Local AI Model Server)
- **Location**: `http://localhost:11434`
- **What happens**:
  - Loads AI model (e.g., `gpt-oss:20b`)
  - Processes messages with system prompt
  - Generates response using local inference
  - Returns response text

### **Step 10: Response Path**
- **Flow**: Ollama → OllamaService → API Route → Frontend
- **Response Format**:
  ```json
  {
    "response": "AI generated response text...",
    "model": "gpt-oss:20b"
  }
  ```

### **Step 11: Display Response**
- **File**: `dashboard/src/pages/ChatPage.tsx`
- **Lines**: 231-257
- **What happens**:
  - Parses response from backend
  - Creates assistant message object
  - Adds to messages state
  - Displays in chat UI

### **Step 12: Save to Memory**
- **File**: `dashboard/src/pages/ChatPage.tsx`
- **Function**: `saveToMemory()` (line 172)
- **API Call**: `POST /api/v1/memory/write`
- **What happens**:
  - Saves user message + AI response
  - Generates embedding (vector)
  - Stores in PostgreSQL
  - Stores embedding in Vector DB (Qdrant)
  - **Future**: Can be retrieved by semantic search

---

## 🔗 Network Flow Summary

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │ ──────▶ │   Backend   │ ──────▶ │   Ollama    │
│ (Frontend)  │         │   (FastAPI) │         │  (LLM API)  │
│ :3000       │         │   :8000     │         │   :11434    │
└─────────────┘         └─────────────┘         └─────────────┘
      │                        │                        │
      │                        │                        │
      ▼                        ▼                        ▼
  React UI              Python Service          Local AI Model
  (ChatPage)            (OllamaService)         (gpt-oss:20b)
```

---

## 📊 Data Structures

### **Request Flow**
```typescript
// Step 1: User Input
userMessage: "What is the weather?"

// Step 2: Memory Context Added
fullPrompt: "Relevant context from shared memory: [Memory...]\n\nUser: What is the weather?"

// Step 3: API Request
POST /api/v1/ollama/simple?message=...&system_message=...&model=gpt-oss:20b

// Step 4: Backend Processing
{
  "messages": [
    {"role": "system", "content": "You are an AI agent..."},
    {"role": "user", "content": "Relevant context...\n\nUser: What is the weather?"}
  ],
  "model": "gpt-oss:20b",
  "temperature": 0.7
}

// Step 5: Ollama Response
{
  "response": "The weather in New York is sunny, 72°F...",
  "model": "gpt-oss:20b"
}
```

---

## 🎯 Key Components

### **Frontend Components**
1. **ChatPage.tsx**: Main chat UI component
2. **api.ts**: API service with Axios
3. **useMemory.ts**: Memory hooks (search, write)
4. **useOllama.ts**: Ollama hooks (models, health)

### **Backend Components**
1. **ollama.py**: FastAPI route handler
2. **ollama_service.py**: Ollama service wrapper
3. **memory.py**: Memory API routes
4. **memory_service.py**: Memory service (search, write)

### **External Services**
1. **Ollama**: Local LLM server (localhost:11434)
2. **PostgreSQL**: Database for memories
3. **Qdrant**: Vector database for embeddings (optional)

---

## 🔍 Debugging Tips

### **Check Console Logs**
- Frontend: Browser DevTools Console
- Backend: Terminal running FastAPI server
- Look for:
  - `🔵 Chat API Call:` - Frontend request
  - `✅ Chat API Response:` - Backend response
  - `❌ Chat API Error:` - Any errors

### **Test Each Step**
1. **Frontend**: Check `handleSend()` is called
2. **Memory Search**: Check `searchMemory()` returns results
3. **API Call**: Check network tab for `/api/v1/ollama/simple`
4. **Backend**: Check FastAPI logs for request
5. **Ollama**: Check Ollama is running (`ollama serve`)
6. **Response**: Check response format matches expected

### **Common Issues**
- **Ollama not running**: Start with `ollama serve`
- **Model not found**: Pull model with `ollama pull gpt-oss:20b`
- **Memory search fails**: Check PostgreSQL connection
- **API timeout**: Increase timeout in `ollama_service.py`

---

## 📝 Summary

**Your chat message follows this path:**

1. **Frontend** (ChatPage.tsx) → User types message
2. **Memory Search** → Searches shared memory for context
3. **Model Selection** → Chooses best AI model
4. **API Call** → Frontend → Backend (localhost:8000)
5. **Backend Route** → FastAPI handler receives request
6. **Ollama Service** → Processes and formats messages
7. **Ollama API** → Backend → Ollama (localhost:11434)
8. **AI Model** → Local LLM generates response
9. **Response Path** → Ollama → Backend → Frontend
10. **Display** → Response shown in chat UI
11. **Save Memory** → Conversation saved to shared memory

**The entire flow is:**
```
User Input → Memory Search → Model Selection → API Call → 
Backend Route → Ollama Service → Ollama API → AI Model → 
Response → Display → Save to Memory
```

---

**Last Updated**: 2024
**Version**: 1.0

