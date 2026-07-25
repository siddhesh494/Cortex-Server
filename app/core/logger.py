import logging
import sys

from app.config import settings


def setup_logger():

    logger = logging.getLogger("fastapi-backend")

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    console = logging.StreamHandler(sys.stdout)

    console.setFormatter(formatter)

    logger.addHandler(console)

    return logger


logger = setup_logger()