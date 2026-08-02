from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_seo_service
from app.services.seo_service import SeoService

router = APIRouter()


@router.get("/sitemap.xml", response_class=Response)
async def get_sitemap(service: Annotated[SeoService, Depends(get_seo_service)]) -> Response:
    """
    Generate dynamic sitemap for search engines.
    Cached for 1 hour.
    """
    content = await service.generate_sitemap()
    return Response(content=content, media_type="application/xml")
