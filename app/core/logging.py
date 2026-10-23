"""Structured logging setup for the application."""

import logging

import sys

from app.core.config import get_settings

def setup_logging() -> None:

    settings = get_settings()

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

                 

    root = logging.getLogger()

    root.setLevel(level)

                                                          

    for h in list(root.handlers):

        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)

    handler.setLevel(level)

    if settings.is_production:

                                   

        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    else:

        fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"

    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root.addHandler(handler)

                                         

    if settings.is_production:

        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger("app").setLevel(level)

