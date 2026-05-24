import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.errors.exceptions import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.error(
        "AppException raised: code=%s status=%d path=%s",
        exc.code.value,
        exc.status,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.status,
        content={
            "success": False,
            "error": {
                "code": exc.code.value,
                "message": exc.message,
                "status": exc.status,
            },
        },
    )
