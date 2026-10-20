"""
Device API-key utilities.

Keys are generated with `secrets` (cryptographically secure), and only
their SHA-256 hash is ever stored -- the plaintext key exists only for
the single moment it's generated and returned to the caller during
registration. This mirrors how you'd handle a password: verify by
hashing the supplied value and comparing hashes, never by storing or
comparing plaintext.
"""
import hashlib
import hmac
import secrets

_API_KEY_BYTES = 32  # 32 random bytes -> a 43-char url-safe token


def generate_api_key() -> str:
    """Generate a new, cryptographically random plaintext API key."""
    return secrets.token_urlsafe(_API_KEY_BYTES)


def hash_api_key(api_key: str) -> str:
    """One-way hash of a plaintext API key, safe to store in the database."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, hashed: str) -> bool:
    """
    Constant-time comparison of a supplied plaintext key against a stored
    hash. Uses hmac.compare_digest to avoid leaking timing information
    that could help an attacker guess the key byte-by-byte.
    """
    return hmac.compare_digest(hash_api_key(api_key), hashed)
