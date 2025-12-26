# Security Module

Cryptographic security utilities for GML Infrastructure.

## Overview

The security module provides production-ready functions for:
- Secure token generation
- JWT token management
- Password hashing and verification
- Decentralized Identifier (DID) generation
- Custom exception handling

All operations use industry-standard cryptographic libraries.

## Core Functions

### Token Generation

#### `generate_token(length: int = 32) -> str`

Generate a cryptographically secure random token.

```python
from src.gml.core.security import generate_token

# Generate a 32-byte token (64 hex characters)
token = generate_token(32)
# Output: "a7f3e9d2b1c8a4f6e2d9b1c7a4f6e3d9"

# Custom length
long_token = generate_token(64)  # 128 hex characters
```

**Use cases:**
- API tokens
- Reset tokens
- Session tokens
- Authentication secrets

#### `generate_api_key() -> str`

Generate a prefixed API key.

```python
from src.gml.core.security import generate_api_key

api_key = generate_api_key()
# Output: "gml_a7f3e9d2b1c8a4f6e2d9b1c7a4f6e3d9"
```

#### `generate_reset_token() -> str`

Generate a password reset token.

```python
from src.gml.core.security import generate_reset_token

reset_token = generate_reset_token()
```

#### `generate_secure_random_string(length: int = 32) -> str`

Alias for `generate_token()`.

```python
from src.gml.core.security import generate_secure_random_string

random_str = generate_secure_random_string(16)
```

### Decentralized Identifiers (DIDs)

#### `generate_did(method: str = "key") -> str`

Generate a W3C-compliant Decentralized Identifier.

```python
from src.gml.core.security import generate_did

# Default key-based DID
did = generate_did()
# Output: "did:key:a7f3e9d2b1c8a4f6e2d9b1c7a4f6e3d9"

# Web-based DID
web_did = generate_did(method="web")
# Output: "did:web:a7f3e9d2b1c8a4f6e2d9b1c7a4f6e3d9"

# Ethereum-based DID
eth_did = generate_did(method="ethr")
# Output: "did:ethr:a7f3e9d2b1c8a4f6e2d9b1c7a4f6e3d9"
```

**Common DID methods:**
- `key` - Key-based, self-managed DIDs
- `web` - Web-based DIDs linked to domain
- `ethr` - Ethereum blockchain-based DIDs

**Format:** `did:{method}:{unique-identifier}`

### Password Hashing

#### `hash_password(password: str) -> str`

Hash a password using bcrypt (12 rounds).

```python
from src.gml.core.security import hash_password

password = "user_password_123"
hashed = hash_password(password)
# Output: "$2b$12$..."
```

**Features:**
- Uses bcrypt with 12 rounds
- Cryptographically secure
- Suitable for database storage

#### `verify_password(plain_password: str, hashed_password: str) -> bool`

Verify a password against a hash.

```python
from src.gml.core.security import verify_password

password = "user_password_123"
hashed = hash_password(password)

# Correct password
verify_password(password, hashed)  # True

# Wrong password
verify_password("wrong_password", hashed)  # False
```

**Security:**
- Uses constant-time comparison (prevents timing attacks)
- Returns False for invalid hashes
- No exceptions on verification failure

#### `hash_multiple_passwords(passwords: list[str]) -> list[str]`

Hash multiple passwords at once.

```python
from src.gml.core.security import hash_multiple_passwords

passwords = ["pass1", "pass2", "pass3"]
hashed_list = hash_multiple_passwords(passwords)
```

#### `verify_multiple_passwords(plain: list[str], hashed: list[str]) -> list[bool]`

Verify multiple password pairs.

```python
from src.gml.core.security import verify_multiple_passwords

plain_passwords = ["pass1", "pass2"]
hashed_passwords = [hash1, hash2]

results = verify_multiple_passwords(plain_passwords, hashed_passwords)
# Output: [True, False] or similar
```

### JWT Token Management

#### `create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str`

Create a signed JWT token.

```python
from src.gml.core.security import create_jwt_token
from datetime import timedelta

# Using default expiration (from settings)
token = create_jwt_token({
    "user_id": "user-123",
    "email": "user@example.com",
    "roles": ["admin"]
})

# Custom expiration
token = create_jwt_token(
    {
        "user_id": "user-456",
        "email": "another@example.com"
    },
    expires_delta=timedelta(hours=48)
)
```

**Features:**
- Signed with application SECRET_KEY
- Uses HS256 algorithm (configurable)
- Automatic expiration timestamp
- Type-safe claims

#### `verify_jwt_token(token: str) -> dict[str, Any]`

Verify and decode a JWT token.

```python
from src.gml.core.security import verify_jwt_token, JWTError_

token = create_jwt_token({"user_id": "123"})

try:
    claims = verify_jwt_token(token)
    print(claims)  # {"user_id": "123", "exp": ..., ...}
except JWTError_:
    print("Invalid or expired token")
```

**Returns:**
- Decoded claims dictionary if valid
- Raises `JWTError_` if invalid/expired

#### `extract_user_id_from_token(token: str) -> Optional[str]`

Safely extract user_id from token (no exceptions).

```python
from src.gml.core.security import extract_user_id_from_token

token = create_jwt_token({"user_id": "user-123"})

user_id = extract_user_id_from_token(token)
# Output: "user-123"

# Invalid token returns None
invalid_id = extract_user_id_from_token("invalid.token")
# Output: None
```

## Exception Handling

### Exception Hierarchy

```
SecurityException (base)
├── TokenGenerationError
├── JWTError_
├── PasswordError
└── DIDError
```

### Using Exceptions

```python
from src.gml.core.security import (
    generate_token,
    TokenGenerationError,
    JWTError_,
    verify_jwt_token,
)

# Token generation
try:
    token = generate_token(0)  # Invalid length
except TokenGenerationError as e:
    print(f"Token generation failed: {e}")

# JWT verification
try:
    claims = verify_jwt_token("invalid.token.here")
except JWTError_ as e:
    print(f"JWT verification failed: {e}")

# Catch all security errors
try:
    verify_jwt_token(token)
except Exception as e:
    print(f"Security operation failed: {e}")
```

## Usage Examples

### User Authentication Flow

```python
from src.gml.core.security import (
    hash_password,
    verify_password,
    create_jwt_token,
    verify_jwt_token,
)

# Registration
user_password = "user_password_123"
hashed_password = hash_password(user_password)
# Store hashed_password in database

# Login
login_password = "user_password_123"
if verify_password(login_password, hashed_password):
    token = create_jwt_token({
        "user_id": user_id,
        "email": email
    })
    # Return token to client

# Token validation
try:
    claims = verify_jwt_token(token)
    user_id = claims.get("user_id")
    # Continue with authenticated request
except JWTError_:
    # Return 401 Unauthorized
    pass
```

### API Key Management

```python
from src.gml.core.security import generate_api_key, hash_password

# Generate API key for user
api_key = generate_api_key()
# Output: "gml_a7f3e9d2b1c8a4f6e2d9b1c7a4f6e3d9"

# Hash it before storage
hashed_api_key = hash_password(api_key)

# Verify incoming API key
def verify_api_key(incoming_key, hashed_stored):
    from src.gml.core.security import verify_password
    return verify_password(incoming_key, hashed_stored)
```

### Password Reset Flow

```python
from src.gml.core.security import generate_reset_token

# User requests password reset
reset_token = generate_reset_token()
# Email reset link to user with token

# User clicks link and provides new password
from src.gml.core.security import hash_password
new_password_hash = hash_password(new_password)
# Update in database

# Verify reset token before allowing reset
from src.gml.core.security import verify_jwt_token, JWTError_

try:
    # If using JWT for reset tokens
    claims = verify_jwt_token(reset_token)
    # Process password reset
except JWTError_:
    # Token invalid or expired
    pass
```

### Session Management

```python
from datetime import timedelta
from src.gml.core.security import (
    create_jwt_token,
    extract_user_id_from_token,
)

# Create session token with custom expiration
session_token = create_jwt_token(
    {
        "user_id": user_id,
        "session_id": session_id,
        "type": "session"
    },
    expires_delta=timedelta(days=7)
)

# Extract user info from session
user_id = extract_user_id_from_token(session_token)
```

### Decentralized Identity

```python
from src.gml.core.security import generate_did

# Create user DID
user_did = generate_did(method="key")
# Store in user profile

# Create organization DID
org_did = generate_did(method="web")

# DIDs can be used for:
# - Self-sovereign identity
# - Credential issuance
# - Decentralized verification
# - Cross-platform identification
```

## Configuration

### JWT Settings

Configure in `.env`:

```bash
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
```

### Password Hashing

Default configuration (12 bcrypt rounds):
- Secure for modern systems
- ~100ms per hash on typical hardware
- Suitable for online authentication

Adjust if needed:

```python
from src.gml.core.security import pwd_context

# Check current configuration
pwd_context.schemes()  # ['bcrypt']
```

## Security Best Practices

### Token Handling

1. **Never log tokens**
   ```python
   # ✗ Bad
   logger.info(f"Token: {token}")

   # ✓ Good
   logger.info(f"Token: {token[:20]}...")
   ```

2. **Use HTTPS only**
   ```python
   # Always transmit tokens over encrypted channels
   ```

3. **Set expiration times**
   ```python
   # ✓ Good
   token = create_jwt_token(data, expires_delta=timedelta(hours=24))
   ```

### Password Handling

1. **Always hash before storage**
   ```python
   # ✓ Good
   hashed = hash_password(user_password)
   db.save(user, hashed_password=hashed)
   ```

2. **Never compare plaintext**
   ```python
   # ✗ Bad
   if user.password == input_password:

   # ✓ Good
   if verify_password(input_password, user.password_hash):
   ```

3. **Clear sensitive data**
   ```python
   # ✓ Good
   password = input()
   verify_password(password, hashed)
   del password  # Clear from memory
   ```

### DID Usage

1. **Use for decentralized identity**
   ```python
   # ✓ Good
   user_did = generate_did(method="key")
   profile.did = user_did
   ```

2. **Store in user profile**
   ```python
   # Link DID to account for credential issuance
   ```

3. **Use method appropriate for context**
   ```python
   # Key method for self-managed identity
   # Web method for organization identity
   # Ethereum method for blockchain integration
   ```

### Error Handling

1. **Catch specific exceptions**
   ```python
   from src.gml.core.security import JWTError_, PasswordError

   try:
       verify_jwt_token(token)
   except JWTError_:
       # Handle JWT-specific error
   except PasswordError:
       # Handle password-specific error
   ```

2. **Don't leak error details**
   ```python
   # ✗ Bad
   except JWTError_ as e:
       return f"Error: {e}"  # Reveals implementation details

   # ✓ Good
   except JWTError_:
       return "Invalid token"
   ```

## Testing

### Example Test Cases

```python
import pytest
from src.gml.core.security import (
    generate_token,
    hash_password,
    verify_password,
    create_jwt_token,
    verify_jwt_token,
    JWTError_,
)

def test_token_generation():
    token = generate_token(32)
    assert len(token) == 64
    assert isinstance(token, str)

def test_password_hashing():
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_jwt_creation_and_verification():
    data = {"user_id": "123"}
    token = create_jwt_token(data)
    claims = verify_jwt_token(token)

    assert claims["user_id"] == "123"

def test_expired_token():
    from datetime import timedelta
    token = create_jwt_token(
        {"user_id": "123"},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )

    with pytest.raises(JWTError_):
        verify_jwt_token(token)
```

## Performance Considerations

- **Token generation**: ~1ms for 32 bytes
- **Password hashing**: ~100ms (by design for security)
- **JWT encoding/decoding**: <1ms
- **JWT verification**: <1ms
- **Password verification**: ~100ms (constant-time comparison)

## Dependencies

- `secrets` - Standard library, secure randomness
- `python-jose` - JWT token handling
- `passlib` - Password hashing abstraction
- `bcrypt` - Bcrypt password hashing (required by passlib)
- `cryptography` - Cryptographic primitives

Install with:
```bash
pip install python-jose passlib bcrypt cryptography
```

## Troubleshooting

### Invalid Token Error

```python
# Check token format
if not token or len(token.split('.')) != 3:
    raise ValueError("Invalid JWT format")

# Check expiration
from src.gml.core.security import verify_jwt_token, JWTError_
try:
    verify_jwt_token(token)
except JWTError_ as e:
    if "expired" in str(e).lower():
        print("Token has expired")
```

### Password Verification Always Fails

```python
# Ensure hash is valid bcrypt format
hash_str = "$2b$12$..."  # Must start with $2a/, $2x$, $2y$, or $2b$

# Test with known values
from src.gml.core.security import hash_password, verify_password
test_pass = "test"
hashed = hash_password(test_pass)
assert verify_password(test_pass, hashed)
```

### DID Generation Issues

```python
# DIDs are always valid if generation succeeds
from src.gml.core.security import generate_did

did = generate_did()  # Always succeeds with default method
assert did.startswith("did:")
```
