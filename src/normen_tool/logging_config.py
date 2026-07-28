from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "normen_tool.log"
DEFAULT_LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_level(log_level: str | int) -> int:
    if isinstance(log_level, int):
        return log_level
    level_name = str(log_level).upper()
    resolved = logging.getLevelName(level_name)
    if isinstance(resolved, int):
        return resolved
    return logging.INFO


def setup_logging(
    log_level: str | int = DEFAULT_LOG_LEVEL,
    log_dir: str | Path | None = None,
    log_file_name: str = DEFAULT_LOG_FILE,
    force: bool = False,
) -> Path:
    resolved_level = _resolve_level(log_level)
    target_dir = (
        Path(log_dir) if log_dir is not None else project_root() / DEFAULT_LOG_DIR
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / log_file_name

    root_logger = logging.getLogger()
    managed_handlers = [
        handler
        for handler in root_logger.handlers
        if getattr(handler, "_normen_tool_managed", False)
    ]

    if managed_handlers and not force:
        return log_file

    if force:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(resolved_level)
    file_handler._normen_tool_managed = True  # type: ignore[attr-defined]

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(resolved_level)
    stream_handler._normen_tool_managed = True  # type: ignore[attr-defined]

    root_logger.setLevel(resolved_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(resolved_level)

    return log_file
