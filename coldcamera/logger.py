from loguru import logger as _logger

from coldcamera.utils.local_path import get_user_local_directory

logger = _logger


DEFAULT_LOG_PATH = str(get_user_local_directory()) + r"\logs\log_{time}.log"
DEFAULT_LOG_FORMAT = "{time:HH:mm:ss.SS} ({file}) [{level}] {message} {exception}"


def initialize_logger():
    """Initialize the logger with the default log path and format."""

    global logger

    logger.add(DEFAULT_LOG_PATH, format=DEFAULT_LOG_FORMAT, colorize=True, catch=True, backtrace=True)
