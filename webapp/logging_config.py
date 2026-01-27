"""Logging configuration for the Heat Pump Potentials webapp."""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger for the webapp.

    Args:
        level: The logging level (default: logging.INFO).

    Returns:
        A configured logger instance.
    """
    # Create logger
    logger = logging.getLogger("heat_pump_webapp")

    # Avoid adding handlers multiple times (Streamlit reruns scripts)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create console handler that writes to stderr (standard for logs)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


# Create a default logger instance for import
logger = setup_logging()
