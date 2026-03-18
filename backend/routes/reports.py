from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from dependencies import get_current_user, get_report_service
from limiter import limiter
from logger import logger
from schemas.report import ReportCreate, ReportResponse
from schemas.user import User
from services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


from typing import Annotated


@router.post("/", response_model=ReportResponse, status_code=201)
@limiter.limit("5/minute")
async def create_report(
    request: Request,
    report_data: ReportCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
) -> dict[str, Any]:
    """
    Submit a report for a photo.

    Raises:
        HTTPException: 500 - If report submission fails.
    """
    try:
        report = await report_service.create_report(
            photo_id=str(report_data.photo_id),
            reporter_id=current_user.id,
            reason=report_data.reason,
            details=report_data.details,
        )
        logger.info(f"Report created by user {current_user.id} against photo {report_data.photo_id}")
        return report

    except Exception as e:
        logger.error(f"Failed to create report: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit report")


@router.get("/my-reports", response_model=list[ReportResponse])
async def list_my_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
) -> list[dict[str, Any]]:
    """
    List reports submitted by the current user.

    Raises:
        HTTPException: 500 - If fetching reports fails.
    """
    try:
        return await report_service.get_user_reports(current_user.id)
    except Exception as e:
        logger.error(f"Failed to list my reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reports")
