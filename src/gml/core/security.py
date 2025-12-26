"""
Security Module for GML Infrastructure

Provides cryptographic utilities for:
- Secure token generation
- Decentralized Identifier (DID) generation
- JWT token creation and verification
- Password hashing and verification

All operations use industry-standard libraries with proper error handling.

Features:
    - Cryptographically secure token generation
    - JWT token management with expiration
    - Password hashing with bcrypt
    - DID generation following W3C standards
    - Custom exception handling
    - Type-safe operations with full type hints
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.gml.core.config import get_settings

# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================


class SecurityException(Exception):
    """Base exception for security operations."""

    pass


class TokenGenerationError(SecurityException):
    """Raised when token generation fails."""

    pass


class JWTError_(SecurityException):
    """Raised when JWT operations fail."""

    pass


class PasswordError(SecurityException):
    """Raised when password operations fail."""

    pass


class DIDError(SecurityException):
    """Raised when DID generation fails."""

    pass


# ============================================================================
# PASSWORD HASHING CONFIGURATION
# ============================================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


# ============================================================================
# TOKEN GENERATION
# ============================================================================


def generate_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Uses Python's secrets module to generate a URL-safe random string
    suitable for API tokens, reset tokens, or other security purposes.

    Args:
        length: Length of the token in bytes (default: 32)

    Returns:
        URL-safe random hex string of specified length

    Raises:
        TokenGenerationError: If token generation fails

    Example:
        >>> token = generate_token(32)
        >>> len(token) == 64  # 32 bytes = 64 hex characters
        True
        >>> isinstance(token, str)
        True
    """
    try:
        if length < 1:
            raise ValueError("Token length must be at least 1 byte")

        return secrets.token_hex(length)
    except Exception as e:
        raise TokenGenerationError(f"Failed to generate token: {str(e)}") from e


# ============================================================================
# DECENTRALIZED IDENTIFIER (DID) GENERATION
# ============================================================================


def generate_did(method: str = "key") -> str:
    """
    Generate a Decentralized Identifier (DID) following W3C standards.

    Creates a unique DID using UUID v4 with the specified method.
    Format: did:{method}:{unique-identifier}

    Common DID methods:
        - key: For key-based DIDs
        - web: For web-based DIDs
        - ethr: For Ethereum-based DIDs

    Args:
        method: DID method identifier (default: "key")

    Returns:
        DID string in format: did:{method}:{uuid}

    Raises:
        DIDError: If DID generation fails

    Example:
        >>> did = generate_did()
        >>> did.startswith("did:key:")
        True
        >>> did = generate_did(method="web")
        >>> did.startswith("did:web:")
        True
    """
    try:
        if not method or not isinstance(method, str):
            raise ValueError("DID method must be a non-empty string")

        unique_id = uuid.uuid4().hex
        did = f"did:{method}:{unique_id}"

        return did
    except Exception as e:
        raise DIDError(f"Failed to generate DID: {str(e)}") from e


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================


def create_jwt_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT token with optional expiration.

    Encodes data into a JWT token signed with the application's secret key.
    Uses HS256 algorithm (configurable via settings).

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional timedelta for token expiration.
                      If None, uses JWT_EXPIRY_HOURS from settings.

    Returns:
        Encoded JWT token string

    Raises:
        JWTError_: If token creation fails

    Example:
        >>> from datetime import timedelta
        >>> token = create_jwt_token(
        ...     {"user_id": "123", "email": "user@example.com"},
        ...     expires_delta=timedelta(hours=24)
        ... )
        >>> isinstance(token, str)
        True

        >>> # Token without explicit expiration (uses settings)
        >>> token = create_jwt_token({"user_id": "456"})
    """
    try:
        settings = get_settings()

        to_encode = data.copy()

        # Set expiration time
        if expires_delta is None:
            expires_delta = timedelta(hours=settings.JWT_EXPIRY_HOURS)

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        return encoded_jwt
    except Exception as e:
        raise JWTError_(f"Failed to create JWT token: {str(e)}") from e


def verify_jwt_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT token.

    Validates the token's signature and expiration. Returns the decoded
    claims if valid.

    Args:
        token: JWT token string to verify

    Returns:
        Dictionary of decoded token claims

    Raises:
        JWTError_: If token verification fails (invalid, expired, etc.)

    Example:
        >>> token = create_jwt_token({"user_id": "123"})
        >>> claims = verify_jwt_token(token)
        >>> claims["user_id"]
        '123'

        >>> # Invalid token raises exception
        >>> try:
        ...     verify_jwt_token("invalid.token.here")
        ... except JWTError_:
        ...     print("Invalid token")
    """
    try:
        settings = get_settings()

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload
    except JWTError as e:
        raise JWTError_(f"Failed to verify JWT token: {str(e)}") from e
    except Exception as e:
        raise JWTError_(f"Unexpected error verifying token: {str(e)}") from e


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id from a JWT token without raising exceptions on invalid tokens.

    Convenience function that safely extracts user_id from a token.
    Returns None if token is invalid or expired.

    Args:
        token: JWT token string

    Returns:
        User ID if token is valid, None otherwise

    Example:
        >>> token = create_jwt_token({"user_id": "123"})
        >>> user_id = extract_user_id_from_token(token)
        >>> user_id
        '123'

        >>> # Returns None for invalid tokens
        >>> user_id = extract_user_id_from_token("invalid")
        >>> user_id is None
        True
    """
    try:
        payload = verify_jwt_token(token)
        return payload.get("user_id")
    except JWTError_:
        return None


# ============================================================================
# PASSWORD HASHING AND VERIFICATION
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Converts a plain text password into a secure bcrypt hash suitable
    for storage in a database. Uses 12 rounds of hashing for security
    without excessive computation time.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string (bcrypt format)

    Raises:
        PasswordError: If hashing fails

    Example:
        >>> hashed = hash_password("my-secure-password")
        >>> isinstance(hashed, str)
        True
        >>> hashed.startswith("$2")  # bcrypt prefix
        True
    """
    try:
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")

        hashed = pwd_context.hash(password)
        return hashed
    except Exception as e:
        raise PasswordError(f"Failed to hash password: {str(e)}") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    Compares a plain text password with a bcrypt hash using the
    secure comparison function to prevent timing attacks.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise

    Raises:
        PasswordError: If verification fails with unexpected error

    Example:
        >>> password = "my-secure-password"
        >>> hashed = hash_password(password)
        >>> verify_password(password, hashed)
        True
        >>> verify_password("wrong-password", hashed)
        False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Most common case is bcrypt.exceptions.InvalidHash
        # which means the hash is invalid but we return False
        if "InvalidHash" in str(type(e)):
            return False
        raise PasswordError(f"Failed to verify password: {str(e)}") from e


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def generate_secure_random_string(length: int = 32) -> str:
    """
    Generate a cryptographically secure random string (alias for generate_token).

    Args:
        length: Length in bytes

    Returns:
        Hex string of specified length
    """
    return generate_token(length)


def generate_api_key() -> str:
    """
    Generate a unique API key suitable for API authentication.

    Format: gml_{random_token}

    Returns:
        API key string

    Example:
        >>> api_key = generate_api_key()
        >>> api_key.startswith("gml_")
        True
    """
    return f"gml_{generate_token(32)}"


def generate_reset_token() -> str:
    """
    Generate a unique password reset token.

    Returns:
        Reset token string

    Example:
        >>> token = generate_reset_token()
        >>> len(token) == 64
        True
    """
    return generate_token(32)


# ============================================================================
# BATCH OPERATIONS
# ============================================================================


def hash_multiple_passwords(passwords: list[str]) -> list[str]:
    """
    Hash multiple passwords.

    Args:
        passwords: List of plain text passwords

    Returns:
        List of hashed passwords

    Raises:
        PasswordError: If any password fails to hash
    """
    hashed = []
    for password in passwords:
        hashed.append(hash_password(password))
    return hashed


def verify_multiple_passwords(
    plain_passwords: list[str],
    hashed_passwords: list[str],
) -> list[bool]:
    """
    Verify multiple password pairs.

    Args:
        plain_passwords: List of plain text passwords
        hashed_passwords: List of hashes to verify against

    Returns:
        List of boolean results (True if matches)

    Raises:
        ValueError: If lists are different lengths
    """
    if len(plain_passwords) != len(hashed_passwords):
        raise ValueError("Lists must be the same length")

    results = []
    for plain, hashed in zip(plain_passwords, hashed_passwords):
        results.append(verify_password(plain, hashed))
    return results


if __name__ == "__main__":
    # Example usage and testing
    print("=" * 60)
    print("SECURITY MODULE - EXAMPLES")
    print("=" * 60)

    # Token generation
    print("\n1. SECURE TOKEN GENERATION")
    token = generate_token(32)
    print(f"   Token: {token}")
    print(f"   Length: {len(token)}")

    # API Key generation
    print("\n2. API KEY GENERATION")
    api_key = generate_api_key()
    print(f"   API Key: {api_key}")

    # DID generation
    print("\n3. DECENTRALIZED IDENTIFIER (DID)")
    did_key = generate_did("key")
    did_web = generate_did("web")
    print(f"   DID (key): {did_key}")
    print(f"   DID (web): {did_web}")

    # Password hashing
    print("\n4. PASSWORD HASHING")
    password = "my-secure-password-123"
    hashed = hash_password(password)
    print(f"   Original: {password}")
    print(f"   Hashed:   {hashed[:50]}...")
    print(f"   Verified: {verify_password(password, hashed)}")
    print(f"   Wrong:    {verify_password('wrong', hashed)}")

    # JWT tokens
    print("\n5. JWT TOKEN MANAGEMENT")
    jwt_token = create_jwt_token(
        {
            "user_id": "user-123",
            "email": "user@example.com",
            "roles": ["admin"],
        }
    )
    print(f"   Token: {jwt_token[:50]}...")

    claims = verify_jwt_token(jwt_token)
    print(f"   Decoded claims: {claims}")
    print(f"   User ID extracted: {extract_user_id_from_token(jwt_token)}")

    print("\n" + "=" * 60)
    print("✓ All examples completed successfully!")
    print("=" * 60)
