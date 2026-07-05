"""
Centralized logging configuration for Jarvis.

Why this exists:
    As this project grows to hundreds of files, you need consistent,
    searchable logs to debug issues — especially once voice, AI calls,
    and integrations are all running concurrently. This module sets up
    one logging configuration that every other module uses, instead of
    each file inventing its own print statements or ad-hoc logger setup.

How it's used elsewhere:
    from backend.core.logging_setup import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")

Design choices:
    - Logs go to BOTH the console (for development) and a rotating file
      (for history/debugging later). Rotating files prevent log files
      from growing forever and filling up disk space.
    - Log level is configurable via settings (LOG_LEVEL env var), so you
      can run with DEBUG locally and INFO in production without code
      changes.
    - __name__ is passed in by each module so log lines show exactly
      which file/module produced them (e.g., "backend.ai.engine").
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from backend.core.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logger() -> None:
    """
    Sets up the root logger once. Safe to call multiple times — only
    does real work the first time (guarded by the _configured flag).
    """
    global _configured
    if _configured:
        return

    log_dir: Path = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler — human-readable output while developing
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler — keeps last 5 files of 5MB each, so logs
    # are preserved for debugging without growing unbounded.
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "jarvis.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger configured for the given module name.

    Usage:
        logger = get_logger(__name__)
    """
    _configure_root_logger()
    return logging.getLogger(name)
