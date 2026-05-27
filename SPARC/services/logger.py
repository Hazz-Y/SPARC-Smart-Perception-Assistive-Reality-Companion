"""
Logger setup for SPARC
Sets up root logger with timestamped, leveled output.
"""
import logging

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures root logger with [timestamp] LEVEL name: message format.
    """
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

