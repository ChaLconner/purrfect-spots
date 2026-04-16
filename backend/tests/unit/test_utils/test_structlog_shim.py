import logging

import structlog


def test_structlog_shim_accepts_keyword_context(caplog):
    logger = structlog.get_logger("tests.structlog")

    with caplog.at_level(logging.ERROR):
        logger.error("structured failure", error="boom", email="test@example.com")

    assert "structured failure" in caplog.text
    assert "error='boom'" in caplog.text
    assert "email='test@example.com'" in caplog.text


def test_structlog_shim_bind_carries_context(caplog):
    logger = structlog.get_logger("tests.structlog").bind(component="gallery")

    with caplog.at_level(logging.INFO):
        logger.info("hello", photo_id="photo-123")

    assert "component='gallery'" in caplog.text
    assert "photo_id='photo-123'" in caplog.text
