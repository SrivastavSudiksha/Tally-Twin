"""
Drop-in replacement for app/api/v1/router.py that includes lab report parse route.
"""

from fastapi import APIRouter

from app.api.v1 import simulations, drugs, health, patients
from app.api.v1 import patients_parse_report  # lab report auto-fill

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(patients.router)
api_router.include_router(patients_parse_report.router)
api_router.include_router(simulations.router)
api_router.include_router(drugs.router)
