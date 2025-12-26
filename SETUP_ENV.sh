#!/bin/bash
# Setup Environment File

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Setting up environment variables..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
    else
        echo "Creating .env file with defaults..."
        cat > .env << 'EOF'
# GML Infrastructure - Environment Configuration
APP_NAME=gml-infrastructure
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database & Infrastructure
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gml_db
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=uploads

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# AI/ML
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama
OLLAMA_MODEL=gpt-oss:20b
USE_OLLAMA=true

# Frontend
VITE_API_URL=http://localhost:8000
EOF
        echo "✅ Created .env file with defaults"
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "Environment setup complete!"
echo ""
echo "To customize, edit: .env"
echo "To see all options, check: .env.example"

