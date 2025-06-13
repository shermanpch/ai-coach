import logging
import os
import sys
from pathlib import Path

from .env import get_logs_dir


def setup_logger(script_file_path: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger for a given script file.

    Args:
        script_file_path: The __file__ path of the script.
        level: The logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        A configured logger instance.
    """
    script_name = os.path.splitext(os.path.basename(script_file_path))[0]
    logs_dir = get_logs_dir()

    # Ensure logs_dir is a Path object if get_logs_dir() returns a string
    if isinstance(logs_dir, str):
        logs_dir = Path(logs_dir)

    log_file = logs_dir / f"{script_name}.log"

    # Create logger
    logger = logging.getLogger(script_name)
    logger.setLevel(level)

    # Create handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add handlers to the logger
    # Clear existing handlers to prevent duplicate messages if this function is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
