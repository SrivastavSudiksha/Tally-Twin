"""Minimal audit log without PII."""

import logging

from datetime import datetime

audit_logger = logging.getLogger("app.audit")

def audit_event(action: str, simulation_id=None, patient_id=None, extra: str = ""):

    audit_logger.info(

        "audit action=%s simulation_id=%s patient_id=%s ts=%s %s",

        action,

        simulation_id,

        patient_id,

        datetime.utcnow().isoformat() + "Z",

        extra,

    )

