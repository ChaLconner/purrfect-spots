import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.gallery_service import GalleryService
from utils.cache import memory_cache

@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    mock_execute = AsyncMock(return_value=MagicMock(data=[{"id": "1", "user_id": "u1", "latitude": 10, "longitude": 10, "tags": ["cute"], "count": 1}]))
    
    mock_single_execute = AsyncMock(return_value=MagicMock(data={"id": "1", "user_id": "u1", "latitude": 10, "longitude": 10}))
    mock_single = MagicMock()
    mock_single.execute = mock_single_execute
    mock_execute.single = mock_single
    
    # We must properly mock SelectQuery methods
    class MockNotWrapper:
        def is_(self, *a, **kw): return mock_eq
    
    mock_not_wrapper = MockNotWrapper()
    
    class MockEq:
        def __init__(self): ...
        def execute(self): return mock_execute()
        def maybe_single(self): return self
        def single(self): return mock_single
        def order(self, *a, **kw): return self
        def limit(self, *a, **kw): return self
        def range(self, *a, **kw): return self
        def gte(self, *a, **kw): return self
        def lte(self, *a, **kw): return self
        def textSearch(self, *a, **kw): return self
        def neq(self, *a, **kw): return self
        def ilike(self, *a, **kw): return self
        def eq(self, *a, **kw): return self
        def is_(self, *a, **kw): return self
        not_ = property(lambda self: mock_not_wrapper)
        def in_(self, *a, **kw): return self
        def update(self, *a, **kw): return self
        def insert(self, *a, **kw): return self
        
    mock_eq = MockEq()
    
    class MockSelect:
        not_ = property(lambda self: mock_not_wrapper)
        def order(self, *a, **kw): return mock_eq
        def limit(self, *a, **kw): return mock_eq
        def eq(self, *a, **kw): return mock_eq
        def gte(self, *a, **kw): return mock_eq
        def lte(self, *a, **kw): return mock_eq
        def textSearch(self, *a, **kw): return mock_eq
        def execute(self): return mock_execute()
        def single(self): return mock_single
        def is_(self, *a, **kw): return mock_eq
        def in_(self, *a, **kw): return mock_eq
        
    mock_select = MockSelect()
    
    class MockTable:
        def select(self, *a, **kw): return mock_select
        def delete(self, *a, **kw): return mock_eq
        def update(self, *a, **kw): return mock_eq
        def insert(self, *a, **kw): return mock_eq
        
    mock_table = MockTable()
    
    mock.table.return_value = mock_table
    mock.rpc.return_value.execute = mock_execute
    return mock

@pytest.fixture
def gallery_service(mock_supabase):
    return GalleryService(supabase_client=mock_supabase)

@pytest.mark.asyncio
async def test_get_all_photos_simple(gallery_service):
    res = await gallery_service.get_all_photos_simple()
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_map_locations(gallery_service):
    res = await gallery_service.get_map_locations()
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_nearby_photos(gallery_service):
    res = await gallery_service.get_nearby_photos(latitude=10, longitude=10, radius_km=5.0)
    assert len(res) == 1

@pytest.mark.asyncio
async def test_search_photos(gallery_service):
    res = await gallery_service.search_photos("cat", limit=10, offset=0)
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_popular_tags(gallery_service):
    memory_cache.clear()
    res = await gallery_service.get_popular_tags()
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_photo_by_id(gallery_service):
    res = await gallery_service.get_photo_by_id("1")
    assert res is not None

@pytest.mark.asyncio
async def test_verify_photo_ownership(gallery_service):
    res = await gallery_service.verify_photo_ownership("1", "u1")
    assert res is not None

@pytest.mark.asyncio
async def test_get_user_photos(gallery_service):
    res = await gallery_service.get_user_photos("u1")
    assert len(res) == 1

@pytest.mark.asyncio
async def test_delete_photo(gallery_service, mock_supabase):
    mock_storage = MagicMock()
    mock_storage.delete_file = AsyncMock()
    try:
        from services.gallery_service import invalidate_gallery_cache
        target = "services.gallery_service.invalidate_gallery_cache"
    except ImportError:
        target = "utils.cache.invalidate_gallery_cache"
        
    with patch(target, new=AsyncMock()), patch("utils.supabase_client.get_async_supabase_admin_client", return_value=mock_supabase):
        await gallery_service.process_photo_deletion("1", "url", "u1", mock_storage)
    assert mock_storage.delete_file.call_count == 0
