"""Application configuration – loads .env **and** Hydra YAML.

Hydra manages all tuneable knobs (model params, chunking, retriever, etc.)
while secrets (API keys) come from ``.env`` via python-dotenv.

This dual approach showcases Hydra's structured-config capability while
keeping credentials out of version control.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
"""Absolute path to the repository root (``project_1_DualLens_Analytics/``)."""

CONF_DIR: Path = PROJECT_ROOT / "conf"
"""Directory containing the Hydra YAML configuration files."""

DATA_DIR: Path = PROJECT_ROOT / "data"
"""Top-level runtime data directory (created at first run)."""

CHROMA_DIR: Path = DATA_DIR / "chroma_db"
"""Persisted ChromaDB vector-store directory."""

PDF_DIR: Path = DATA_DIR / "pdfs"
"""Directory where extracted PDF documents are stored."""

ZIP_PATH: Path = PROJECT_ROOT / "notebooks" / "Companies-AI-Initiatives.zip"
"""Path to the ZIP archive containing the AI-initiative PDF reports."""

# ---------------------------------------------------------------------------
# Hydra config loader (called once, cached)
# ---------------------------------------------------------------------------
_hydra_cfg: DictConfig | None = None


def get_hydra_cfg() -> DictConfig:
    """Load ``conf/config.yaml`` via OmegaConf (Hydra-compatible).

    We use OmegaConf directly so the Streamlit app (which has its own
    entry-point) can still benefit from structured YAML config without
    requiring ``@hydra.main``.
    """
    global _hydra_cfg
    if _hydra_cfg is None:
        yaml_path = CONF_DIR / "config.yaml"
        logger.info("Loading Hydra config from %s", yaml_path)
        _hydra_cfg = OmegaConf.load(yaml_path)  # type: ignore[assignment]
        logger.debug("Hydra config loaded: %s", OmegaConf.to_yaml(_hydra_cfg))
    return _hydra_cfg  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Convenience accessors (keep existing constants for backward compat)
# ---------------------------------------------------------------------------
def _cfg_list(key: str) -> list[str]:
    """Resolve a top-level Hydra config key to a plain Python list.

    Args:
        key: Top-level key in ``conf/config.yaml`` whose value is a YAML
            list (e.g. ``"companies"``, ``"financial_metrics"``).

    Returns:
        A plain ``list[str]`` with variable interpolation resolved.
    """
    return OmegaConf.to_container(get_hydra_cfg()[key], resolve=True)  # type: ignore[return-value]


@property  # Not used as descriptor – simple function
def DEFAULT_COMPANIES() -> list[str]:  # noqa: N802
    return _cfg_list("companies")


DEFAULT_MODEL: str = "gpt-4o-mini"  # overridden by Hydra at runtime
DEFAULT_EMBEDDING_MODEL: str = "text-embedding-ada-002"
STOCK_PERIOD: str = "3y"

FINANCIAL_METRICS: list[str] = [
    "Market Cap",
    "P/E Ratio",
    "Dividend Yield",
    "Beta",
    "Total Revenue",
]


# ---------------------------------------------------------------------------
# Settings dataclass – populated from **both** .env and Hydra YAML
# ---------------------------------------------------------------------------
@dataclass
class Settings:
    """Runtime settings assembled from Hydra config + environment secrets.

    This dataclass is the single source of truth for every tuneable
    parameter consumed at runtime.  It is populated by :func:`load_settings`,
    which merges ``.env`` secrets with the Hydra YAML file.

    Attributes:
        api_key: OpenAI-compatible API key (sourced from ``.env``).
        api_base: Base URL for the LLM endpoint (sourced from ``.env``).
        model: Chat-completion model identifier (e.g. ``"gpt-4o-mini"``).
        embedding_model: Embedding model identifier
            (e.g. ``"text-embedding-ada-002"``).
        temperature: Sampling temperature for the LLM (0 = deterministic).
        max_tokens: Maximum number of tokens in the LLM response.
        top_p: Nucleus-sampling probability mass.
        frequency_penalty: Penalises repeated token sequences.
        chunk_size: Target token count per document chunk.
        chunk_overlap: Overlap in tokens between consecutive chunks.
        encoding_name: Tiktoken encoding used for chunking
            (e.g. ``"cl100k_base"``).
        retriever_k: Number of top-*k* documents returned by the retriever.
        search_type: ChromaDB search strategy (``"similarity"`` or
            ``"mmr"``).
        collection_name: Name of the ChromaDB collection.
        companies: Ticker symbols of companies to analyse.
        stock_period: Yahoo-Finance period string (e.g. ``"3y"``).
        financial_metrics: Column labels shown on dashboards and reports.
    """

    # secrets (from .env)
    api_key: str = ""
    api_base: str = ""

    # LLM (from Hydra)
    model: str = DEFAULT_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    temperature: float = 0.0
    max_tokens: int = 5000
    top_p: float = 0.95
    frequency_penalty: float = 1.2

    # chunking (from Hydra)
    chunk_size: int = 1000
    chunk_overlap: int = 200
    encoding_name: str = "cl100k_base"

    # retriever (from Hydra)
    retriever_k: int = 10
    search_type: str = "similarity"

    # vector store
    collection_name: str = "AI_Initiatives"

    # companies
    companies: list[str] = field(default_factory=lambda: ["GOOGL", "MSFT", "IBM", "NVDA", "AMZN"])

    # stock
    stock_period: str = "3y"

    # financial metrics
    financial_metrics: list[str] = field(
        default_factory=lambda: [
            "Market Cap",
            "P/E Ratio",
            "Dividend Yield",
            "Beta",
            "Total Revenue",
        ]
    )

    # --- helpers -----------------------------------------------------------
    def apply_env(self) -> None:
        """Push ``api_key`` and ``api_base`` into ``os.environ``.

        LangChain reads ``OPENAI_API_KEY`` and ``OPENAI_BASE_URL``
        from the environment, so this method bridges our dataclass
        with the library's expectations.
        """
        logger.info("Applying API credentials to os.environ")
        os.environ["OPENAI_API_KEY"] = self.api_key
        os.environ["OPENAI_BASE_URL"] = self.api_base
        logger.debug("OPENAI_BASE_URL=%s", self.api_base)


def load_settings() -> Settings:
    """Build a :class:`Settings` instance from ``.env`` secrets and Hydra YAML.

    The function performs two steps:

    1. Loads ``.env`` via ``python-dotenv`` to make ``API_KEY`` and
       ``OPENAI_API_BASE`` available in ``os.environ``.
    2. Reads ``conf/config.yaml`` through :func:`get_hydra_cfg` and maps
       every section to the corresponding :class:`Settings` field.

    Returns:
        A fully populated :class:`Settings` dataclass.
    """
    # 1. secrets from .env
    logger.info("Loading .env from %s", PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / ".env")

    # 2. structured config from Hydra YAML
    cfg = get_hydra_cfg()

    logger.info(
        "Building Settings: model=%s, chunk_size=%d, retriever_k=%d",
        cfg.llm.model,
        cfg.chunking.chunk_size,
        cfg.retriever.k,
    )
    return Settings(
        # secrets
        api_key=os.getenv("API_KEY", ""),
        api_base=os.getenv("OPENAI_API_BASE", ""),
        # LLM
        model=cfg.llm.model,
        temperature=cfg.llm.temperature,
        max_tokens=cfg.llm.max_tokens,
        top_p=cfg.llm.top_p,
        frequency_penalty=cfg.llm.frequency_penalty,
        embedding_model=cfg.embedding.model,
        # chunking
        chunk_size=cfg.chunking.chunk_size,
        chunk_overlap=cfg.chunking.chunk_overlap,
        encoding_name=cfg.chunking.encoding_name,
        # retriever
        retriever_k=cfg.retriever.k,
        search_type=cfg.retriever.search_type,
        # vector store
        collection_name=cfg.vector_store.collection_name,
        # companies & stock
        companies=OmegaConf.to_container(cfg.companies, resolve=True),  # type: ignore[arg-type]
        stock_period=cfg.stock.period,
        # financial metrics
        financial_metrics=OmegaConf.to_container(cfg.financial_metrics, resolve=True),  # type: ignore[arg-type]
    )
