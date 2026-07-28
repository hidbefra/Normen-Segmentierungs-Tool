from __future__ import annotations

import logging

from normen_tool.logging_config import setup_logging


def test_setup_logging_creates_log_file(tmp_path):
    log_file = setup_logging(log_level="DEBUG", log_dir=tmp_path, force=True)

    logger = logging.getLogger("normen_tool.tests")
    logger.debug("hello log")

    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_file.exists()
    assert "hello log" in log_file.read_text(encoding="utf-8")
