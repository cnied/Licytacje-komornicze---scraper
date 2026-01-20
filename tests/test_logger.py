import pytest
import logging
from pathlib import Path


def test_setup_logger_returns_logger():
    from src.logger import setup_logger
    logger = setup_logger("test_logger_1")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_1"


def test_setup_logger_same_name_returns_same_instance():
    from src.logger import setup_logger
    logger1 = setup_logger("same_name_logger")
    logger2 = setup_logger("same_name_logger")

    assert logger1 is logger2


def test_setup_logger_different_names_return_different_instances():
    from src.logger import setup_logger
    logger1 = setup_logger("logger_a")
    logger2 = setup_logger("logger_b")

    assert logger1 is not logger2
    assert logger1.name != logger2.name


def test_setup_logger_creates_logs_directory():
    from src.logger import setup_logger
    setup_logger("dir_test_logger")

    assert Path("logs").exists()
    assert Path("logs").is_dir()


def test_setup_logger_level_is_debug():
    from src.logger import setup_logger
    logger = setup_logger("level_test_logger")

    assert logger.level == logging.DEBUG


def test_setup_logger_has_handlers():
    from src.logger import setup_logger
    logger = setup_logger("handler_test_logger")

    assert len(logger.handlers) > 0


def test_setup_logger_has_console_handler():
    from src.logger import setup_logger
    logger = setup_logger("console_handler_test")

    has_stream_handler = any(
        isinstance(h, logging.StreamHandler) for h in logger.handlers
    )
    assert has_stream_handler


def test_setup_logger_has_file_handler():
    from src.logger import setup_logger
    logger = setup_logger("file_handler_test")

    has_file_handler = any(
        isinstance(h, logging.FileHandler) for h in logger.handlers
    )
    assert has_file_handler


def test_setup_logger_default_name():
    from src.logger import setup_logger
    logger = setup_logger()

    assert logger.name == "scraper"


def test_setup_logger_does_not_duplicate_handlers():
    from src.logger import setup_logger

    # Wywołaj setup_logger wielokrotnie z tą samą nazwą
    logger = setup_logger("no_duplicate_test")
    initial_handler_count = len(logger.handlers)

    setup_logger("no_duplicate_test")
    setup_logger("no_duplicate_test")

    # Liczba handlerów nie powinna się zwiększyć
    assert len(logger.handlers) == initial_handler_count
