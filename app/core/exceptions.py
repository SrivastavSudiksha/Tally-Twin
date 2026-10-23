from typing import Any, Optional

from fastapi import HTTPException, Request, status

from fastapi.responses import JSONResponse

from fastapi.exceptions import RequestValidationError

from starlette.exceptions import HTTPException as StarletteHTTPException

import logging

logger = logging.getLogger(__name__)

class DigitalTwinException(Exception):

    """Base application exception."""

    def __init__(self, message: str, code: str = "app_error"):

        self.message = message

        self.code = code

        super().__init__(self.message)

class PatientDataError(DigitalTwinException):

    def __init__(self, message: str):

        super().__init__(message, code="patient_data_error")

class DrugNotFoundError(DigitalTwinException):

    def __init__(self, message: str):

        super().__init__(message, code="drug_not_found")

class SimulationError(DigitalTwinException):

    def __init__(self, message: str):

        super().__init__(message, code="simulation_error")

def error_body(

    code: str,

    message: str,

    details: Any = None,

    status_code: int = 400,

) -> dict:

    body: dict = {

        "error": {

            "code": code,

            "message": message,

        }

    }

    if details is not None:

        body["error"]["details"] = details

    return body

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:

    return JSONResponse(

        status_code=exc.status_code,

        content=error_body(

            code="http_error",

            message=str(exc.detail),

            status_code=exc.status_code,

        ),

    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:

    return JSONResponse(

        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,

        content=error_body(

            code="validation_error",

            message="Request validation failed",

            details=exc.errors(),

        ),

    )

async def app_exception_handler(request: Request, exc: DigitalTwinException) -> JSONResponse:

    logger.warning("App error: %s – %s", exc.code, exc.message)

    return JSONResponse(

        status_code=status.HTTP_400_BAD_REQUEST,

        content=error_body(code=exc.code, message=exc.message),

    )

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:

    logger.exception("Unhandled error on %s %s", request.method, request.url.path)

    return JSONResponse(

        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

        content=error_body(

            code="internal_error",

            message="An unexpected error occurred",

        ),

    )

