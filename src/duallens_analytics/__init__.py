"""DualLens Analytics – RAG-powered investment analysis."""

import logging

__version__ = "0.1.0"

# ── Package-level logging setup ────────────────────────────────────────────
# Consumers can adjust the level via logging.getLogger("duallens_analytics").
logging.getLogger(__name__).addHandler(logging.NullHandler())


def configure_logging(
    level: int = logging.INFO,
    fmt: str = "%(asctime)s | %(name)-35s | %(levelname)-8s | %(message)s",
) -> None:
    """Configure the root *duallens_analytics* logger.

    Call this once at application start-up (e.g. in ``app.py`` or ``cli.py``).
    """
    logger = logging.getLogger("duallens_analytics")
    logger.setLevel(level)
    # Remove the default NullHandler so the StreamHandler takes effect
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.NullHandler)
        for h in logger.handlers
    ):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
