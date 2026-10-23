from fastapi import APIRouter

from fastapi.responses import JSONResponse

from app.core.config import get_settings

from app.db.session import check_db_connection

router = APIRouter(tags=["Health"])

@router.get("/health")

async def health_check():

    """
    Liveness + readiness style check.
    Returns 200 if process is up; includes DB status.
    """

    settings = get_settings()

    db_ok = check_db_connection()

    body = {

        "status": "ok" if db_ok else "degraded",

        "app": settings.APP_NAME,

        "version": settings.APP_VERSION,

        "environment": settings.ENVIRONMENT,

        "checks": {

            "database": "up" if db_ok else "down",

        },

    }

    status_code = 200 if db_ok else 503

    return JSONResponse(content=body, status_code=status_code)

@router.get("/ready")

async def readiness():

    """Kubernetes-style readiness: fail if DB is down."""

    if not check_db_connection():

        return JSONResponse(

            status_code=503,

            content={"status": "not_ready", "reason": "database_unavailable"},

        )

    return {"status": "ready"}

