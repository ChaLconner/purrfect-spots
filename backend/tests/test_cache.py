"""
Tests for caching utilities
"""

from unittest.mock import MagicMock, patch

from utils import cache


class TestCacheUtils:
    """Test suite for cache utilities"""

    def setup_method(self):
        """Reset caches before each test"""
        cache.invalidate_all_caches()

    def test_generate_cache_key(self):
        """Test cache key generation"""
        key1 = cache.generate_cache_key("arg1", kwarg1="val1")
        key2 = cache.generate_cache_key("arg1", kwarg1="val1")
        key3 = cache.generate_cache_key("arg2", kwarg1="val1")

        assert key1 == key2
        assert key1 != key3

    def test_cached_gallery_decorator(self):
        """Test gallery caching"""
        mock_func = MagicMock(return_value="data")
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_gallery(mock_func)

        # First call - miss
        result1 = decorated("a")
        assert result1 == "data"
        mock_func.assert_called_once()

        # Second call - hit
        result2 = decorated("a")
        assert result2 == "data"
        mock_func.assert_called_once()  # Call count shouldn't increase

        # Different arg - miss
        result3 = decorated("b")
        assert result3 == "data"
        assert mock_func.call_count == 2

    def test_cached_tags_decorator(self):
        """Test tags caching"""
        mock_func = MagicMock(return_value=["tag1"])
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_tags(mock_func)

        # First call - miss
        result1 = decorated()
        assert result1 == ["tag1"]
        mock_func.assert_called_once()

        # Second call - hit
        result2 = decorated()
        assert result2 == ["tag1"]
        mock_func.assert_called_once()

    def test_cached_user_photos_decorator(self):
        """Test user photos caching with user_id extraction"""
        mock_func = MagicMock(return_value=["photo1"])
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_user_photos(mock_func)

        # Call with user_id kwarg
        result1 = decorated(user_id="user1")
        assert result1 == ["photo1"]
        mock_func.assert_called_once()

        # Hit
        result2 = decorated(user_id="user1")
        assert result2 == ["photo1"]
        mock_func.assert_called_once()

        # Different user
        result3 = decorated(user_id="user2")
        assert result3 == ["photo1"]
        assert mock_func.call_count == 2

    def test_invalidate_gallery_cache(self):
        """Test gallery cache invalidation"""
        mock_func = MagicMock(return_value="data")
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_gallery(mock_func)

        decorated("a")
        cache.invalidate_gallery_cache()
        decorated("a")

        assert mock_func.call_count == 2

    def test_invalidate_user_cache_specific(self):
        """Test invalidating specific user cache"""
        mock_func = MagicMock(return_value="data")
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_user_photos(mock_func)

        decorated(user_id="u1")
        decorated(user_id="u2")

        cache.invalidate_user_cache(user_id="u1")

        # u1 should be miss (invalidated)
        decorated(user_id="u1")
        assert mock_func.call_count == 3

        # u2 should be hit (not invalidated)
        decorated(user_id="u2")
        assert mock_func.call_count == 3

    def test_invalidate_user_cache_all(self):
        """Test invalidating all user caches"""
        mock_func = MagicMock(return_value="data")
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_user_photos(mock_func)

        decorated(user_id="u1")
        decorated(user_id="u2")

        cache.invalidate_user_cache()

        decorated(user_id="u1")
        decorated(user_id="u2")

        assert mock_func.call_count == 4

    def test_get_cache_stats(self):
        """Test stats retrieval"""
        stats = cache.get_cache_stats()
        # Always have mode and redis_connected
        assert "mode" in stats
        assert "redis_connected" in stats

        # When not using Redis (memory mode), should have detailed stats
        if stats["mode"] == "memory":
            assert "gallery" in stats
            assert "tags" in stats
            assert "user_photos" in stats
            assert stats["gallery"]["maxsize"] == 50

    @patch("utils.cache.is_dev", return_value=True)
    def test_logging_in_dev(self, mock_is_dev):
        """Test that hits/misses are logged in dev mode"""
        with patch("utils.cache.logger") as mock_logger:
            mock_func = MagicMock(return_value="val")
            mock_func.__name__ = "mock_func"
            decorated = cache.cached_gallery(mock_func)

            # Miss
            decorated("x")
            assert mock_logger.debug.call_count >= 1

            # Hit
            decorated("x")
            assert mock_logger.debug.call_count >= 2
