import logging
import sys
from crawler import config


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("cb_crawler")
    if logger.handlers:
        return logger

    logger.setLevel(config.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
