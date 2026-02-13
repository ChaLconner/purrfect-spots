from fastapi import APIRouter, Depends, Response
from supabase import Client

from dependencies import get_supabase_client
from services.seo_service import SeoService

router = APIRouter()

@router.get("/sitemap.xml", response_class=Response)
async def get_sitemap(
    supabase: Client = Depends(get_supabase_client)
) -> Response:
    """
    Generate dynamic sitemap for search engines.
    Cached for 1 hour.
    """
    service = SeoService(supabase)
    content = await service.generate_sitemap()
    
    return Response(content=content, media_type="application/xml")
