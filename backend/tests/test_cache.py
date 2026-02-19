from unittest.mock import AsyncMock, patch

import pytest

from utils import cache

pytestmark = pytest.mark.asyncio


class TestCacheUtils:
    @pytest.fixture(autouse=True)
    async def clear_cache_fixture(self):
        """Reset caches before each test"""
        await cache.invalidate_all_caches()
        yield

    def test_generate_cache_key(self):
        key1 = cache.generate_cache_key("arg1", kwarg1="val1")
        key2 = cache.generate_cache_key("arg1", kwarg1="val1")
        assert key1 == key2

    async def test_cached_gallery_decorator(self):
        mock_func = AsyncMock(return_value="data")
        mock_func.__name__ = "mock_func"
        # Force a unique prefix for this test instance
        decorated = cache.cache(key_prefix="test_gallery")(mock_func)

        # 1st call - miss
        res1 = await decorated("a")
        assert res1 == "data"
        assert mock_func.call_count == 1

        # 2nd call - hit
        res2 = await decorated("a")
        assert res2 == "data"
        assert mock_func.call_count == 1

        # 3rd call - miss (different arg)
        res3 = await decorated("b")
        assert res3 == "data"
        assert mock_func.call_count == 2

    async def test_invalidate_gallery_cache(self):
        mock_func = AsyncMock(return_value="data")
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_gallery(mock_func)

        await decorated("client", "a")
        assert mock_func.call_count == 1

        await cache.invalidate_gallery_cache()

        await decorated("client", "a")
        assert mock_func.call_count == 2

    async def test_invalidate_user_cache_all(self):
        mock_func = AsyncMock(return_value="data")
        mock_func.__name__ = "mock_func"
        decorated = cache.cached_user_photos(mock_func)

        await decorated("client", user_id="u1")
        await decorated("client", user_id="u2")
        assert mock_func.call_count == 2

        await cache.invalidate_user_cache()

        await decorated("client", user_id="u1")
        await decorated("client", user_id="u2")
        assert mock_func.call_count == 4

    async def test_get_cache_stats(self):
        stats = cache.get_cache_stats()
        assert "mode" in stats
        if stats["mode"] == "memory":
            assert "gallery" in stats

    async def test_logging_in_dev(self):
        with patch("utils.cache.is_dev", True), patch("utils.cache.logger") as mock_logger:
            mock_func = AsyncMock(return_value="val")
            mock_func.__name__ = "mock_func"
            decorated = cache.cached_gallery(mock_func)

            await decorated("client", "x")
            assert mock_logger.debug.call_count >= 1  # Miss log

            await decorated("client", "x")
            assert mock_logger.debug.call_count >= 2  # Hit log
