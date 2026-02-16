"""Hydra CLI entry-point for DualLens Analytics.

This module showcases Hydra's ``@hydra.main`` decorator for structured
configuration.  Run it with:

    poetry run python -m duallens_analytics.cli          # uses conf/config.yaml defaults
    poetry run python -m duallens_analytics.cli llm.model=gpt-4o  # override from CLI
    poetry run python -m duallens_analytics.cli --cfg job         # print resolved config

The Streamlit app (``app.py``) loads the same YAML via OmegaConf directly
because Streamlit manages its own entry-point.
"""

from __future__ import annotations

import logging
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from duallens_analytics import configure_logging

logger = logging.getLogger(__name__)

# Resolve absolute path to conf/ so Hydra works regardless of cwd
_CONF_DIR = str(Path(__file__).resolve().parents[2] / "conf")


@hydra.main(version_base=None, config_path=_CONF_DIR, config_name="config")
def main(cfg: DictConfig) -> None:
    """Print the resolved Hydra config and run a quick smoke-test."""
    configure_logging()
    logger.info("Hydra CLI started")
    print("=" * 60)
    print("  DualLens Analytics – Hydra Config")
    print("=" * 60)
    print(OmegaConf.to_yaml(cfg))
    print("=" * 60)

    # Quick sanity checks
    print(f"LLM model    : {cfg.llm.model}")
    print(f"Chunk size   : {cfg.chunking.chunk_size}")
    print(f"Retriever k  : {cfg.retriever.k}")
    print(f"Companies    : {list(cfg.companies)}")
    print(f"Stock period : {cfg.stock.period}")


if __name__ == "__main__":
    main()
