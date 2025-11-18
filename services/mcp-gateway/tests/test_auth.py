"""Tests for authentication modules."""

import pytest
from jose import jwt
from fastapi import HTTPException

from app.auth.jwt import create_access_token, verify_token
from app.auth.hmac import compute_signature, verify_signature
from app.config import settings


class TestJWT:
    """Test JWT authentication."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        payload = {"sub": "test-user", "role": "admin"}
        token = create_access_token(payload)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        decoded = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        assert decoded["sub"] == "test-user"
        assert decoded["role"] == "admin"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_verify_valid_token(self):
        """Test verification of valid token."""
        payload = {"sub": "test-user"}
        token = create_access_token(payload)

        result = verify_token(token)

        assert result["sub"] == "test-user"

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_verify_expired_token(self):
        """Test verification of expired token."""
        from datetime import timedelta

        # Create token that expires immediately
        payload = {"sub": "test-user"}
        token = create_access_token(payload, expires_delta=timedelta(seconds=-1))

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)

        assert exc_info.value.status_code == 401


class TestHMAC:
    """Test HMAC signature validation."""

    def test_compute_signature(self):
        """Test HMAC signature computation."""
        payload = b"test payload"
        signature = compute_signature(payload)

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex = 64 chars

    def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        payload = b"test payload"
        signature = compute_signature(payload)

        assert verify_signature(payload, signature) is True

    def test_verify_invalid_signature(self):
        """Test verification of invalid signature."""
        payload = b"test payload"
        wrong_signature = "0" * 64

        assert verify_signature(payload, wrong_signature) is False

    def test_verify_modified_payload(self):
        """Test that modified payload fails verification."""
        payload = b"original payload"
        signature = compute_signature(payload)

        modified_payload = b"modified payload"

        assert verify_signature(modified_payload, signature) is False
