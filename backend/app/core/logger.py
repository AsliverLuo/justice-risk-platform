import logging
import sys


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.setLevel(level)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
