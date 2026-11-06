import sys
from loguru import logger
from app.core.config import settings

logger.remove()

log_level = getattr(settings.app, "log_level", "INFO").upper()

logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level=log_level,
    colorize=True,
    enqueue=True,
)
