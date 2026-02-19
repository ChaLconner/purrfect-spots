
"""
Additional tests for auth middleware focusing on permission checks
"""

import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from middleware.auth_middleware import require_permission
from user_models.user import User

@pytest.mark.asyncio
async def test_require_permission_direct_success():
    """Test user has direct permission"""
    # User(id=..., email=..., name=...) are required
    user = User(
        id="123", 
        email="test@example.com", 
        name="Test User",
        permissions=["content:write"],
        role="user"
    )
    
    checker = require_permission("content:write")
    # The checker is a dependency function that takes a user
    # In FastAPI, it resolves the user first. Here we call it directly passing the user?
    # No, require_permission returns a callable that takes (user: User = Depends(get_current_user)).
    # We can simulate the dependency injection by calling the returned function and passing the user directly 
    # IF the function signature allows it. 
    # looking at auth_middleware.py:
    # async def permission_checker(user: User = Depends(get_current_user)) -> User:
    # So we can pass `user` as a keyword argument or positional if it's the first arg.
    
    result = await checker(user=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_permission_admin_bypass():
    """Test admin role bypasses permission check"""
    user = User(
        id="123", 
        email="admin@example.com", 
        name="Admin User",
        permissions=[],
        role="admin"
    )
    
    checker = require_permission("content:write")
    result = await checker(user=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_permission_super_admin_bypass():
    """Test super_admin role bypasses permission check"""
    user = User(
        id="123", 
        email="super@example.com", 
        name="Super Admin",
        permissions=[],
        role="super_admin"
    )
    
    checker = require_permission("content:write")
    result = await checker(user=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_permission_fail():
    """Test failure when no permission and not admin"""
    user = User(
        id="123", 
        email="user@example.com", 
        name="Normal User",
        permissions=["other:permission"],
        role="user"
    )
    
    checker = require_permission("content:write")
    with pytest.raises(HTTPException) as exc:
        await checker(user=user)
    assert exc.value.status_code == 403
