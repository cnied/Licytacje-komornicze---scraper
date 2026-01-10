import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name: str ="scraper") -> logging.Logger:
    """
    Konfiguracja loggera dla apki
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s | %(levelname)s-8s | %(name)s | %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_filename = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

