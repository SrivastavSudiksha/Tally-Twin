"""Digital Twin PK Backend – FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.exceptions import (
    DigitalTwinException,
    http_exception_handler,
    validation_exception_handler,
    app_exception_handler,
    unhandled_exception_handler,
)
from app.api.v1.router import api_router
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Individualized PK-based risk estimator for clinicians. "
            "Input patient health data + drug composition/regimen → "
            "predicted exposure, organ flags, DDI, and downloadable PDF report. "
            "Research / educational tool only — not a medical device."
        ),
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DigitalTwinException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": settings.docs_url,
            "health": f"{settings.API_V1_PREFIX}/health",
            "positioning": "Individualized PK-based risk estimator (in-silico dosing simulator)",
        }

    return app


app = create_app()
