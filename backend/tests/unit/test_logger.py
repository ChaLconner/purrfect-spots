import logging

from app.logger import setup_logger


def test_vercel_nonproduction_logger_uses_stdout_only(monkeypatch, tmp_path) -> None:
    logger_name = "purrfect_spots.test_vercel_nonproduction"
    test_logger = logging.getLogger(logger_name)
    test_logger.handlers.clear()

    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.chdir(tmp_path)

    configured_logger = setup_logger(logger_name)

    try:
        assert not any(isinstance(handler, logging.FileHandler) for handler in configured_logger.handlers)
    finally:
        for handler in configured_logger.handlers:
            handler.close()
        configured_logger.handlers.clear()
