# Render Deployment Guide (Supabase-First)

## Quick Setup

### 1. Create Web Service on Render
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
- **Start Command**: `uvicorn src.gml.api.main:app --host 0.0.0.0 --port $PORT`

### 2. Required Environment Variables

Set these in Render → Environment:

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<generate-32+-random-bytes>

# Supabase (REQUIRED - Primary Database)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=<supabase-anon-key>
SUPABASE_SERVICE_KEY=<supabase-service-role-key>

# Direct Postgres (for migrations only)
DATABASE_URL=postgresql://postgres.your-project-id:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Qdrant Cloud
QDRANT_URL=<qdrant-cloud-url>
QDRANT_API_KEY=<qdrant-cloud-api-key>

# CORS
CORS_ORIGINS=https://your-app.vercel.app

# LLM (optional)
OPENAI_API_KEY=<optional>
LLM_PROVIDER=openai

# Redis (optional - leave empty for degraded mode)
REDIS_URL=
```

### 3. Supabase Setup

**Required Tables** (create via Supabase SQL Editor or migrations):
```sql
-- Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    capabilities TEXT[],
    status TEXT DEFAULT 'active',
    api_token TEXT UNIQUE,
    did TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memories table
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id TEXT UNIQUE NOT NULL,
    agent_id UUID REFERENCES agents(id),
    conversation_id TEXT,
    content JSONB NOT NULL,
    memory_type TEXT NOT NULL,
    tags TEXT[],
    visibility TEXT DEFAULT 'private',
    readable_by TEXT[],
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content JSONB NOT NULL,
    metadata JSONB,
    used_memories TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Notes

- **SUPABASE_URL**: Get from Supabase Dashboard → Project Settings → API
- **SUPABASE_ANON_KEY**: Public key (for client-side, if needed)
- **SUPABASE_SERVICE_KEY**: Secret key (for server-side operations)
- **DATABASE_URL**: Pooled connection string for Alembic migrations only
- **CORS_ORIGINS**: Set to your Vercel frontend URL
- **REDIS_URL**: Leave unset to run without cache (degraded mode)

### 5. Database Migrations

Migrations run automatically in the build command using Alembic with DATABASE_URL.
- Use Render's Shell: `alembic upgrade head`

### 6. Health Check

Render will use `/health` endpoint by default. Your app already has this.

## Managed Services Used

| Service | Purpose | Notes |
|---------|---------|-------|
| Supabase | Primary Database | REST API + Postgres |
| Qdrant Cloud | Vector DB | Create collection on first run |
| (Redis) | Caching | Optional - skip for initial deploy |

## Troubleshooting

- **Build fails**: Check `requirements.txt` for any platform-specific deps
- **Supabase connection fails**: Verify SUPABASE_URL and SERVICE_KEY
- **Migration fails**: Check DATABASE_URL (pooled connection string)
- **CORS errors**: Ensure CORS_ORIGINS includes your Vercel URL exactly
