"""Production-ready logging configuration."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        datefmt="%Y-%m-%d %H:%M:%S",
    )
