"""
Example: Security Module Usage

This script demonstrates practical usage of the security module
for authentication, token management, and password handling.
"""

from datetime import timedelta

from src.gml.core.security import (
    create_jwt_token,
    extract_user_id_from_token,
    generate_api_key,
    generate_did,
    generate_reset_token,
    generate_token,
    hash_password,
    verify_jwt_token,
    verify_password,
    JWTError_,
)


def example_token_generation():
    """Generate different types of secure tokens."""
    print("=" * 60)
    print("TOKEN GENERATION EXAMPLES")
    print("=" * 60)

    # Basic token
    token = generate_token(32)
    print(f"Secure Token (32 bytes):")
    print(f"  {token}")
    print(f"  Length: {len(token)} chars")

    # API Key
    api_key = generate_api_key()
    print(f"\nAPI Key:")
    print(f"  {api_key}")

    # Reset Token
    reset_token = generate_reset_token()
    print(f"\nPassword Reset Token:")
    print(f"  {reset_token}")

    # Custom length token
    long_token = generate_token(64)
    print(f"\nLong Token (64 bytes):")
    print(f"  {long_token[:40]}...")
    print(f"  Length: {len(long_token)} chars")


def example_did_generation():
    """Generate Decentralized Identifiers."""
    print("\n" + "=" * 60)
    print("DECENTRALIZED IDENTIFIER (DID) EXAMPLES")
    print("=" * 60)

    # Key-based DID
    did_key = generate_did(method="key")
    print(f"DID (key method):")
    print(f"  {did_key}")
    print(f"  Format: did:key:{{uuid}}")

    # Web-based DID
    did_web = generate_did(method="web")
    print(f"\nDID (web method):")
    print(f"  {did_web}")

    # Ethereum-based DID
    did_ethr = generate_did(method="ethr")
    print(f"\nDID (ethereum method):")
    print(f"  {did_ethr}")

    print("\nDID Use Cases:")
    print("  - Self-sovereign identity")
    print("  - Credential issuance")
    print("  - Decentralized verification")
    print("  - Cross-platform identification")


def example_password_hashing():
    """Demonstrate password hashing and verification."""
    print("\n" + "=" * 60)
    print("PASSWORD HASHING EXAMPLES")
    print("=" * 60)

    password = "MySecurePassword123!"

    # Hash password
    hashed = hash_password(password)
    print(f"Original Password: {password}")
    print(f"Hashed Password: {hashed}")
    print(f"Hash Length: {len(hashed)} characters")

    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"\nVerify Correct Password: {is_valid}")

    # Verify wrong password
    is_valid = verify_password("WrongPassword", hashed)
    print(f"Verify Wrong Password: {is_valid}")

    # Multiple password verification
    print("\nMultiple Passwords:")
    from src.gml.core.security import hash_multiple_passwords

    passwords = ["pass1", "pass2", "pass3"]
    hashed_list = hash_multiple_passwords(passwords)
    print(f"  Hashed {len(hashed_list)} passwords")

    from src.gml.core.security import verify_multiple_passwords

    results = verify_multiple_passwords(
        ["pass1", "pass2", "pass3"], hashed_list
    )
    print(f"  Verification results: {results}")


def example_jwt_tokens():
    """Create and verify JWT tokens."""
    print("\n" + "=" * 60)
    print("JWT TOKEN EXAMPLES")
    print("=" * 60)

    # Create a basic token
    print("1. Basic JWT Token:")
    token = create_jwt_token({"user_id": "user-123"})
    print(f"   Token: {token[:50]}...")

    # Verify the token
    claims = verify_jwt_token(token)
    print(f"   Verified Claims: {claims}")

    # Create token with custom data
    print("\n2. JWT Token with Custom Data:")
    token_with_data = create_jwt_token(
        {
            "user_id": "user-456",
            "email": "user@example.com",
            "roles": ["admin", "editor"],
            "organization_id": "org-789",
        }
    )
    print(f"   Token: {token_with_data[:50]}...")

    claims = verify_jwt_token(token_with_data)
    print(f"   User ID: {claims.get('user_id')}")
    print(f"   Email: {claims.get('email')}")
    print(f"   Roles: {claims.get('roles')}")

    # Create token with custom expiration
    print("\n3. JWT Token with Custom Expiration:")
    token_48h = create_jwt_token(
        {"user_id": "user-789"},
        expires_delta=timedelta(hours=48),
    )
    print(f"   Token (48 hour expiry): {token_48h[:50]}...")

    # Token with short expiration
    token_short = create_jwt_token(
        {"user_id": "user-short"},
        expires_delta=timedelta(minutes=30),
    )
    print(f"   Token (30 minute expiry): {token_short[:50]}...")

    # Extract user ID
    print("\n4. Extract User ID from Token:")
    user_id = extract_user_id_from_token(token_with_data)
    print(f"   Extracted User ID: {user_id}")

    # Safe extraction with invalid token
    invalid_user_id = extract_user_id_from_token("invalid.token.here")
    print(f"   Extract from Invalid Token: {invalid_user_id}")


def example_authentication_flow():
    """Demonstrate a complete authentication flow."""
    print("\n" + "=" * 60)
    print("AUTHENTICATION FLOW EXAMPLE")
    print("=" * 60)

    print("\n1. User Registration:")
    user_email = "john@example.com"
    user_password = "SecurePass123!"

    hashed_password = hash_password(user_password)
    print(f"   Email: {user_email}")
    print(f"   Password Hash: {hashed_password}")
    print("   (Hash would be stored in database)")

    print("\n2. User Login:")
    login_email = "john@example.com"
    login_password = "SecurePass123!"

    # Verify password
    if verify_password(login_password, hashed_password):
        print("   ✓ Password verified")

        # Create session token
        session_token = create_jwt_token(
            {
                "user_id": "user-john",
                "email": login_email,
                "session_type": "web",
            },
            expires_delta=timedelta(hours=24),
        )
        print(f"   ✓ Session token created")
        print(f"   Token: {session_token[:50]}...")
    else:
        print("   ✗ Password verification failed")

    print("\n3. Token Verification (subsequent requests):")
    try:
        claims = verify_jwt_token(session_token)
        print("   ✓ Token verified")
        print(f"   User: {claims.get('email')}")
        print(f"   User ID: {claims.get('user_id')}")
        print("   ✓ Request authorized")
    except JWTError_:
        print("   ✗ Token invalid or expired")

    print("\n4. Logout (invalidate token):")
    print("   (Token would be removed from client)")
    print("   (Server would remove from whitelist if needed)")


def example_api_key_management():
    """Demonstrate API key generation and verification."""
    print("\n" + "=" * 60)
    print("API KEY MANAGEMENT EXAMPLE")
    print("=" * 60)

    print("\n1. Generate API Key:")
    api_key = generate_api_key()
    print(f"   Generated: {api_key}")

    print("\n2. Hash for Storage:")
    hashed_api_key = hash_password(api_key)
    print(f"   Hashed: {hashed_api_key}")
    print("   (Store this hashed version in database)")

    print("\n3. Verify Incoming API Key:")
    incoming_key = api_key  # Simulating incoming request

    if verify_password(incoming_key, hashed_api_key):
        print(f"   ✓ API Key verified")
        print(f"   Request authorized")
    else:
        print(f"   ✗ Invalid API Key")


def example_password_reset():
    """Demonstrate password reset flow."""
    print("\n" + "=" * 60)
    print("PASSWORD RESET FLOW EXAMPLE")
    print("=" * 60)

    print("\n1. User Requests Reset:")
    reset_token = generate_reset_token()
    print(f"   Reset Token: {reset_token}")
    print("   (Send reset link via email)")

    print("\n2. User Submits New Password:")
    new_password = "NewPassword123!"
    new_hash = hash_password(new_password)
    print(f"   New Password Hash: {new_hash}")
    print("   (Update in database)")

    print("\n3. Verify Reset Token:")
    # In production, you might store reset token as JWT
    print(f"   ✓ Token valid")
    print(f"   ✓ Password updated")

    print("\n4. Login with New Password:")
    login_password = "NewPassword123!"
    if verify_password(login_password, new_hash):
        print(f"   ✓ New password verified")
        print(f"   ✓ User logged in successfully")


def example_error_handling():
    """Demonstrate error handling."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING EXAMPLES")
    print("=" * 60)

    print("\n1. Invalid Token:")
    try:
        verify_jwt_token("invalid.token.structure")
    except JWTError_ as e:
        print(f"   Caught: {type(e).__name__}")
        print(f"   Message: {str(e)[:50]}...")

    print("\n2. Expired Token:")
    # Create a token that expires immediately
    expired_token = create_jwt_token(
        {"user_id": "test"},
        expires_delta=timedelta(seconds=-1),
    )

    try:
        verify_jwt_token(expired_token)
    except JWTError_ as e:
        print(f"   Caught: {type(e).__name__}")
        print(f"   Message: {str(e)[:50]}...")

    print("\n3. Invalid Password Hash:")
    try:
        verify_password("password", "not-a-valid-hash")
    except Exception as e:
        print(f"   Result: False (no exception)")

    print("\n4. Invalid Token Length:")
    from src.gml.core.security import generate_token, TokenGenerationError

    try:
        generate_token(0)  # Invalid length
    except TokenGenerationError as e:
        print(f"   Caught: {type(e).__name__}")
        print(f"   Message: {str(e)}")


if __name__ == "__main__":
    try:
        example_token_generation()
        example_did_generation()
        example_password_hashing()
        example_jwt_tokens()
        example_authentication_flow()
        example_api_key_management()
        example_password_reset()
        example_error_handling()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
