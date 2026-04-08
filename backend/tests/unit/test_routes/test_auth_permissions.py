"""
Additional tests for auth middleware focusing on permission checks
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from middleware.auth_middleware import require_permission
from schemas.user import User


@pytest.mark.asyncio
async def test_require_permission_direct_success():
    """Test user has direct permission"""
    # User(id=..., email=..., name=...) are required
    user = User(id="123", email="test@example.com", name="Test User", permissions=["content:write"], role="user")

    checker = require_permission("content:write")
    # Mock request is required by permission_checker
    mock_request = MagicMock()
    mock_request.url.path = "/test"

    result = await checker(request=mock_request, user=user)
    assert result == user


@pytest.mark.asyncio
async def test_require_permission_admin_bypass():
    """Test admin role bypasses permission check"""
    user = User(id="123", email="admin@example.com", name="Admin User", permissions=[], role="admin")

    checker = require_permission("content:write")
    mock_request = MagicMock()
    mock_request.url.path = "/test"
    result = await checker(request=mock_request, user=user)
    assert result == user


@pytest.mark.asyncio
async def test_require_permission_super_admin_bypass():
    """Test super_admin role bypasses permission check"""
    user = User(id="123", email="super@example.com", name="Super Admin", permissions=[], role="super_admin")

    checker = require_permission("content:write")
    mock_request = MagicMock()
    mock_request.url.path = "/test"
    result = await checker(request=mock_request, user=user)
    assert result == user


@pytest.mark.asyncio
async def test_require_permission_fail():
    """Test failure when no permission and not admin"""
    user = User(id="123", email="user@example.com", name="Normal User", permissions=["other:permission"], role="user")

    checker = require_permission("content:write")
    mock_request = MagicMock()
    mock_request.url.path = "/test"
    with pytest.raises(HTTPException) as exc:
        await checker(request=mock_request, user=user)
    assert exc.value.status_code == 403
