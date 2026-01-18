import logging
from logging.handlers import RotatingFileHandler
import pathlib
import sys

logger = logging.getLogger(__name__)


# Handling of uncaught exceptions
# def handle_exception(exc_type, exc_value, exc_traceback):
#     if issubclass(exc_type, KeyboardInterrupt):
#         sys.__excepthook__(exc_type, exc_value, exc_traceback)
#         return

#     logger.error("Uncaught exception", exc_info=(exc_type,
#                                                  exc_value,
#                                                  exc_traceback))


# # Set exception handler
# sys.excepthook = handle_exception


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up and return a logger with the specified name and level.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    log_path = pathlib.Path('./loggs')
    log_path.mkdir(parents=True, exist_ok=True)

    fh = RotatingFileHandler(filename=log_path / 'rag_with_crawl4ai.log',
                             mode='a', maxBytes=61440, backupCount=10,
                             encoding='utf-8', delay=True)
    ch = logging.StreamHandler()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.info(f"Logger initialized with level {logging.getLevelName(level)}")

    return logger
