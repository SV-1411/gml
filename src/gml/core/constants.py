"""
Application Constants

Centralized constants used throughout the GML Infrastructure application.
"""

# ============================================================================
# AGENT CONSTANTS
# ============================================================================

VALID_AGENT_STATUSES = ["active", "inactive", "error", "maintenance"]
DEFAULT_AGENT_STATUS = "inactive"

# ============================================================================
# MESSAGE CONSTANTS
# ============================================================================

VALID_MESSAGE_STATUSES = ["pending", "delivered", "failed", "timeout", "expired"]
DEFAULT_MESSAGE_STATUS = "pending"
DEFAULT_MESSAGE_TIMEOUT_SECONDS = 60
DEFAULT_MESSAGE_MAX_RETRIES = 3

# ============================================================================
# MEMORY CONSTANTS
# ============================================================================

VALID_MEMORY_TYPES = ["episodic", "semantic", "procedural"]
VALID_MEMORY_VISIBILITY = ["all", "private", "organization"]
DEFAULT_MEMORY_VISIBILITY = "all"
EMBEDDING_DIMENSIONS = 1536  # OpenAI text-embedding-3-small dimensions

# ============================================================================
# COST CONSTANTS
# ============================================================================

COST_MATRIX = {
    "agent_registration": 0.01,
    "message_send": 0.01,
    "memory_write": 0.02,
    "memory_search": 0.05,
}

# ============================================================================
# API CONSTANTS
# ============================================================================

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
MAX_PAGINATION_LIMIT = 100
DEFAULT_PAGINATION_LIMIT = 100
DEFAULT_PAGINATION_OFFSET = 0

# ============================================================================
# SECURITY CONSTANTS
# ============================================================================

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
API_KEY_PREFIX = "gml_"
DID_METHOD = "key"

# ============================================================================
# DATABASE CONSTANTS
# ============================================================================

DATABASE_POOL_SIZE_DEV = 5
DATABASE_POOL_SIZE_PROD = 20
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600

# ============================================================================
# REDIS CONSTANTS
# ============================================================================

REDIS_DEFAULT_TTL = 3600  # 1 hour
REDIS_MESSAGE_CHANNEL = "gml:messages"
REDIS_HEARTBEAT_CHANNEL = "gml:heartbeat"

# ============================================================================
# QDRANT CONSTANTS
# ============================================================================

QDRANT_COLLECTION_NAME = "gml_memories"
QDRANT_VECTOR_SIZE = EMBEDDING_DIMENSIONS
QDRANT_DISTANCE_METRIC = "Cosine"

# ============================================================================
# HEALTH CHECK CONSTANTS
# ============================================================================

HEALTH_CHECK_TIMEOUT = 5.0  # seconds

# ============================================================================
# LOGGING CONSTANTS
# ============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = "INFO"

