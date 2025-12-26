# Environment Variables Setup

This guide explains how to set up environment variables for the GML Infrastructure Dashboard.

## Important: Vite Environment Variables

**Vite uses the `VITE_` prefix** (not `REACT_APP_`). All environment variables must start with `VITE_` to be accessible in the application.

## Quick Setup

### 1. Create `.env` file

Create a `.env` file in the `dashboard/` directory with the following content:

```bash
# GML Infrastructure Dashboard - Environment Variables
# Development Configuration

# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000

# WebSocket Configuration
VITE_WS_URL=http://localhost:8000
VITE_WS_PATH=/ws

# Environment
VITE_ENV=development
```

### 2. Create `.env.production` file (for production builds)

```bash
# GML Infrastructure Dashboard - Production Environment Variables

# API Configuration
VITE_API_URL=https://api.yourdomain.com
VITE_API_BASE_URL=https://api.yourdomain.com

# WebSocket Configuration
VITE_WS_URL=https://api.yourdomain.com
VITE_WS_PATH=/ws

# Environment
VITE_ENV=production
```

## Environment Variables Reference

| Variable | Description | Default | Example |
|---------|-------------|---------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` | `https://api.yourdomain.com` |
| `VITE_API_BASE_URL` | Alternative API URL (fallback) | `http://localhost:8000` | `https://api.yourdomain.com` |
| `VITE_WS_URL` | WebSocket server URL | `http://localhost:8000` | `wss://api.yourdomain.com` |
| `VITE_WS_PATH` | WebSocket path | `/ws` | `/ws` |
| `VITE_ENV` | Environment mode | `development` | `production` |

## Usage in Code

Environment variables are accessed via `import.meta.env`:

```typescript
// API Service
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// WebSocket Service
const wsUrl = import.meta.env.VITE_WS_URL || 'http://localhost:8000';
const wsPath = import.meta.env.VITE_WS_PATH || '/ws';
```

## Development vs Production

### Development (`.env`)
- Uses `http://localhost:8000` for API
- Uses `ws://localhost:8000/ws` for WebSocket
- Hot module replacement enabled
- Detailed error messages

### Production (`.env.production`)
- Uses HTTPS URLs for API
- Uses WSS (secure WebSocket) for WebSocket
- Optimized builds
- Minified code

## Building for Production

```bash
# Build with production environment
npm run build

# The build will use .env.production if it exists
# Otherwise, it will use .env
```

## Testing API Endpoints

Before running the dashboard, test that the backend is working:

```bash
# Run automated test script
./test-api.sh

# Or test manually
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/detailed
```

See `API_TESTING.md` for detailed testing instructions.

## Security Notes

1. **Never commit `.env` files** - They are already in `.gitignore`
2. **Use `.env.example`** - Create a template file without sensitive values
3. **Production secrets** - Store production secrets in secure vaults (not in files)
4. **HTTPS/WSS** - Always use secure protocols in production

## Troubleshooting

### Variables not working?

1. **Check prefix**: Must start with `VITE_`
2. **Restart dev server**: Changes require restart: `npm run dev`
3. **Check file location**: `.env` must be in `dashboard/` root
4. **Check syntax**: No spaces around `=` sign

### WebSocket not connecting?

1. **Check URL**: Verify `VITE_WS_URL` and `VITE_WS_PATH`
2. **Check protocol**: Use `ws://` for HTTP, `wss://` for HTTPS
3. **Check backend**: Ensure WebSocket server is running
4. **Check CORS**: Backend must allow WebSocket connections

## Example Files

### `.env` (Development)
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
VITE_WS_PATH=/ws
VITE_ENV=development
```

### `.env.production` (Production)
```bash
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=https://api.yourdomain.com
VITE_WS_PATH=/ws
VITE_ENV=production
```

### `.env.example` (Template)
```bash
# Copy this file to .env and update values
VITE_API_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
VITE_WS_PATH=/ws
VITE_ENV=development
```

