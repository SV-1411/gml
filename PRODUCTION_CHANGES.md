# GML Production Deployment Changes
# Track all changes made for Vercel + Render + Supabase deployment

## 2026-04-05 - Implementation Phase

### 1. Deterministic Qdrant Point IDs
**File**: `src/gml/services/memory_store.py`
**Change**: Replaced Python's randomized `hash()` with deterministic SHA-256-based integer mapping
**Reason**: Python's `hash()` is randomized per process, breaking stability across restarts
**Lines**: 31 (added `import hashlib`), 470-485 (updated `_context_id_to_point_id` method)

### 2. Configurable CORS Origins
**File**: `src/gml/core/config.py`
**Change**: Added `CORS_ORIGINS` setting (comma-separated list) and `cors_origins_list` property
**Reason**: Production needs restricted CORS to Vercel frontend URL instead of allowing all origins
**Lines**: 99-108 (new CORS_ORIGINS field and property)

**File**: `src/gml/api/middleware.py`
**Change**: Updated CORS middleware to use `settings.cors_origins_list` instead of `["*"]`
**Reason**: Security - restrict CORS to known frontend origins
**Lines**: 22-42 (updated setup_middleware function)

### 3. Redis Optional (Degraded Mode)
**File**: `src/gml/cache/redis_client.py`
**Change**: Made Redis optional - `get_redis_client()` returns None if not configured or connection fails
**Reason**: Production can run without Redis (no caching), useful for initial deployment without Upstash
**Lines**: 715-766 (updated singleton pattern, added `is_redis_available()` helper)

**File**: `src/gml/services/embedding_service.py`
**Change**: Updated cache methods to handle None from `get_redis_client()` gracefully
**Reason**: Embedding service must work without Redis cache
**Lines**: 167-184 (`_get_cached_embedding`), 197-209 (`_cache_embedding`), 677-683 (`clear_cache`)

### 4. Supabase Migration (MAJOR)
**Files**: All API routes and services converted to use Supabase

**New Files Created**:
- `src/gml/services/supabase_client.py` - Supabase async client wrapper
- `src/gml/api/dependencies.py` - FastAPI dependency for SupabaseDB

**Routes Updated** (SQLAlchemy → Supabase):
- `src/gml/api/routes/memory.py` - Memory CRUD operations
- `src/gml/api/routes/agents.py` - Agent management
- `src/gml/api/routes/chat.py` - Chat with memory injection
- `src/gml/api/routes/conversations.py` - Conversation management
- `src/gml/api/routes/storage.py` - File storage (Supabase Storage)
- `src/gml/api/routes/search.py` - Search operations
- `src/gml/api/routes/memory_versions.py` - Memory versioning
- `src/gml/api/routes/batch_operations.py` - Batch operations

**Services Updated**:
- `src/gml/services/conversation_tracker.py` - Uses SupabaseDB

**Dependencies**:
- `requirements.txt` - Added `supabase==2.7.4`, marked SQLAlchemy as migration-only

### 5. Render Deployment Documentation
**File**: `RENDER_DEPLOY.md`
**Change**: Created deployment guide with Supabase-first configuration
**Contents**: Build command, start command, required env vars, Supabase table schemas

### 6. Environment Configuration
**File**: `.env.example`
**Change**: Updated for Supabase-first configuration
**Contents**: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY as primary

---

## Final Status

| Component | Status | Notes |
|-----------|--------|-------|
| Qdrant Point IDs | ✅ Done | Deterministic SHA-256 hash |
| CORS Origins | ✅ Done | Configurable via CORS_ORIGINS env var |
| Redis Optional | ✅ Done | App runs without Redis |
| Supabase Client | ✅ Done | Primary database access |
| API Routes | ✅ Done | All routes use SupabaseDB |
| Services | ✅ Done | Conversation tracker updated |
| Render Deploy | ✅ Done | RENDER_DEPLOY.md created |
| Environment | ✅ Done | .env.example updated |

---

## Environment Variables for Production

```
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<key>
SUPABASE_SERVICE_KEY=<key>
DATABASE_URL=<for-migrations-only>
QDRANT_URL=<qdrant-cloud-url>
QDRANT_API_KEY=<key>
CORS_ORIGINS=https://your-app.vercel.app
SECRET_KEY=<random-32+-bytes>

# Optional
REDIS_URL=  # Leave empty for degraded mode
OPENAI_API_KEY=<key>
```

---
