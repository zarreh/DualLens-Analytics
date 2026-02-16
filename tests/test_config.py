"""Unit tests for duallens_analytics.config – Hydra + dotenv integration."""

from __future__ import annotations

import os

from omegaconf import DictConfig

from duallens_analytics.config import (
    CHROMA_DIR,
    CONF_DIR,
    DATA_DIR,
    PDF_DIR,
    PROJECT_ROOT,
    ZIP_PATH,
    Settings,
    get_hydra_cfg,
    load_settings,
)


# ── Paths -----------------------------------------------------------------
class TestPaths:
    def test_project_root_exists(self):
        assert PROJECT_ROOT.exists()

    def test_conf_dir_exists(self):
        assert CONF_DIR.exists()

    def test_zip_path_exists(self):
        assert ZIP_PATH.exists()

    def test_data_dirs_under_project(self):
        assert str(DATA_DIR).startswith(str(PROJECT_ROOT))
        assert str(CHROMA_DIR).startswith(str(DATA_DIR))
        assert str(PDF_DIR).startswith(str(DATA_DIR))


# ── Hydra config ----------------------------------------------------------
class TestHydraConfig:
    def test_get_hydra_cfg_returns_dictconfig(self):
        cfg = get_hydra_cfg()
        assert isinstance(cfg, DictConfig)

    def test_cfg_has_required_keys(self):
        cfg = get_hydra_cfg()
        for key in (
            "llm",
            "embedding",
            "chunking",
            "retriever",
            "vector_store",
            "companies",
            "stock",
            "financial_metrics",
        ):
            assert key in cfg, f"Missing key: {key}"

    def test_llm_defaults(self):
        cfg = get_hydra_cfg()
        assert cfg.llm.model == "gpt-4o-mini"
        assert cfg.llm.temperature == 0.0
        assert cfg.llm.max_tokens == 5000

    def test_chunking_defaults(self):
        cfg = get_hydra_cfg()
        assert cfg.chunking.chunk_size == 1000
        assert cfg.chunking.chunk_overlap == 200
        assert cfg.chunking.encoding_name == "cl100k_base"

    def test_retriever_defaults(self):
        cfg = get_hydra_cfg()
        assert cfg.retriever.k == 10
        assert cfg.retriever.search_type == "similarity"

    def test_companies_list(self):
        cfg = get_hydra_cfg()
        companies = list(cfg.companies)
        assert len(companies) == 5
        assert "NVDA" in companies

    def test_financial_metrics_list(self):
        cfg = get_hydra_cfg()
        metrics = list(cfg.financial_metrics)
        assert "Market Cap" in metrics
        assert "Beta" in metrics


# ── Settings dataclass ----------------------------------------------------
class TestSettings:
    def test_default_construction(self):
        s = Settings()
        assert s.model == "gpt-4o-mini"
        assert s.chunk_size == 1000
        assert s.retriever_k == 10
        assert len(s.companies) == 5

    def test_apply_env_sets_os_environ(self):
        s = Settings(api_key="test-key", api_base="https://example.com/v1")
        s.apply_env()
        assert os.environ["OPENAI_API_KEY"] == "test-key"
        assert os.environ["OPENAI_BASE_URL"] == "https://example.com/v1"

    def test_custom_fields(self):
        s = Settings(
            model="gpt-4o",
            temperature=0.5,
            chunk_size=500,
            retriever_k=5,
            companies=["AAPL"],
        )
        assert s.model == "gpt-4o"
        assert s.temperature == 0.5
        assert s.chunk_size == 500
        assert s.retriever_k == 5
        assert s.companies == ["AAPL"]


# ── load_settings ---------------------------------------------------------
class TestLoadSettings:
    def test_load_settings_returns_settings(self):
        settings = load_settings()
        assert isinstance(settings, Settings)

    def test_load_settings_reads_hydra_values(self):
        settings = load_settings()
        assert settings.model == "gpt-4o-mini"
        assert settings.chunk_size == 1000

    def test_load_settings_reads_env(self):
        """Env vars from .env are loaded (value may be empty in CI)."""
        settings = load_settings()
        # At minimum these should be strings (possibly empty)
        assert isinstance(settings.api_key, str)
        assert isinstance(settings.api_base, str)
