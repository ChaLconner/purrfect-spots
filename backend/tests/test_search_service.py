from unittest.mock import MagicMock

import pytest

from services.search_service import SearchService


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    # Mock table("cat_photos")
    client.table.return_value = client
    client.select.return_value = client
    client.is_.return_value = client
    client.order.return_value = client
    client.range.return_value = client
    client.limit.return_value = client
    client.execute.return_value = MagicMock(data=[])
    
    # Mock filters
    client.or_.return_value = client
    client.contains.return_value = client
    client.text_search.return_value = client
    client.filter.return_value = client
    client.eq.return_value = client
    
    # Mock RPC
    client.rpc.return_value = client
    return client

@pytest.fixture
def search_service(mock_supabase):
    return SearchService(mock_supabase)

def test_check_fulltext_support_success(mock_supabase):
    # Setup
    mock_supabase.execute.return_value = MagicMock(data=[{"search_vector": ""}])
    
    service = SearchService(mock_supabase)
    assert service._fulltext_available is True

def test_check_fulltext_support_failure(mock_supabase):
    # Setup - raise exception
    mock_supabase.execute.side_effect = Exception("Column not found")
    
    service = SearchService(mock_supabase)
    assert service._fulltext_available is False

def test_search_photos_fulltext(mock_supabase, search_service):
    # Setup
    search_service._fulltext_available = True
    expected_data = [{"id": "1", "location_name": "Cat Cafe"}]
    mock_supabase.execute.return_value = MagicMock(data=expected_data)
    
    # Execute
    results = search_service.search_photos(query="cafe", limit=10)
    
    # Verify
    assert results == expected_data
    # Should call rpc or text_search depending on implementation of _fulltext_search
    # Here we assume it calls rpc first as per code
    mock_supabase.rpc.assert_called_with(
        "search_cat_photos", 
        {"search_query": "cafe", "result_limit": 10, "result_offset": 0}
    )

def test_search_photos_ilike_fallback(mock_supabase, search_service):
    # Setup
    search_service._fulltext_available = False # Force fallback
    expected_data = [{"id": "2", "location_name": "Park"}]
    mock_supabase.execute.return_value = MagicMock(data=expected_data)
    
    # Execute
    results = search_service.search_photos(query="park")
    
    # Verify
    assert results == expected_data
    # Should use table().select()...
    mock_supabase.table.assert_called_with("cat_photos")

def test_search_photos_with_tags(mock_supabase, search_service):
    # Setup
    search_service._fulltext_available = False
    mock_supabase.execute.return_value = MagicMock(data=[])
    
    # Execute
    search_service.search_photos(tags=["#Cute", "Outdoor"])
    
    # Verify
    # Check that contains was called
    # clean_tags should be ['cute', 'outdoor']
    # args[0] is 'tags', args[1] is list
    call_args = mock_supabase.contains.call_args
    assert call_args is not None
    assert call_args[0][0] == "tags"
    assert "cute" in call_args[0][1]
    assert "outdoor" in call_args[0][1]
