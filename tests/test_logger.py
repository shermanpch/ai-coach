"""
Test logging utility for CSE-6748 project tests.
Provides centralized logging functionality for test execution tracking.
"""

import logging
from datetime import datetime
from pathlib import Path


def setup_test_logger(test_name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger for a specific test.

    Args:
        test_name: Name of the test (will be used for log filename)
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    # Ensure logs directory exists
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Create timestamp for log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{test_name}_{timestamp}.log"
    log_path = log_dir / log_filename

    # Create logger
    logger = logging.getLogger(f"test_{test_name}")

    # Clear any existing handlers
    logger.handlers = []

    # Set logging level
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (for real-time feedback)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Log initial message
    logger.info(f"=== Starting test: {test_name} ===")
    logger.info(f"Log file: {log_path}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")

    return logger


def log_test_step(
    logger: logging.Logger, step_num: int, description: str, details: str = None
):
    """
    Log a test step with consistent formatting.

    Args:
        logger: Logger instance
        step_num: Step number
        description: Step description
        details: Optional additional details
    """
    logger.info(f"STEP {step_num}: {description}")
    if details:
        logger.info(f"  Details: {details}")


def log_test_result(
    logger: logging.Logger, test_name: str, success: bool, details: str = None
):
    """
    Log test result with summary.

    Args:
        logger: Logger instance
        test_name: Name of the test
        success: Whether test passed
        details: Optional additional details
    """
    status = "PASSED" if success else "FAILED"
    logger.info(f"=== Test {test_name} {status} ===")
    if details:
        logger.info(f"  Details: {details}")


def log_metrics(logger: logging.Logger, metrics: dict):
    """
    Log test metrics in a structured format.

    Args:
        logger: Logger instance
        metrics: Dictionary of metrics to log
    """
    logger.info("=== Test Metrics ===")
    for key, value in metrics.items():
        logger.info(f"  {key}: {value}")


def cleanup_old_logs(days_to_keep: int = 7):
    """
    Clean up old log files to prevent disk space issues.

    Args:
        days_to_keep: Number of days of logs to keep (default: 7)
    """
    log_dir = Path(__file__).parent / "logs"
    if not log_dir.exists():
        return

    cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

    for log_file in log_dir.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                print(f"Deleted old log file: {log_file.name}")
            except OSError:
                print(f"Failed to delete log file: {log_file.name}")


if __name__ == "__main__":
    # Example usage and cleanup
    print("Test Logger Utility")
    print("===================")

    # Clean up old logs
    cleanup_old_logs()

    # Example logger setup
    logger = setup_test_logger("example_test")
    log_test_step(logger, 1, "Initialize test environment")
    log_metrics(logger, {"documents_created": 5, "processing_time": "2.3s"})
    log_test_result(logger, "example_test", True, "All assertions passed")
