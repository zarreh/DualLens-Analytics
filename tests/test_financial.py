"""Unit tests for duallens_analytics.financial."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from duallens_analytics.financial import (
    fetch_metrics,
    fetch_stock_history,
    plot_metric_comparison,
    plot_metrics_radar,
    plot_stock_trends,
)


@pytest.mark.slow
class TestFetchStockHistory:
    """These tests hit the Yahoo Finance API – marked ``slow``."""

    def test_returns_dict(self):
        result = fetch_stock_history(["IBM"], period="1mo")
        assert isinstance(result, dict)
        assert "IBM" in result

    def test_dataframe_has_close(self):
        result = fetch_stock_history(["IBM"], period="1mo")
        assert "Close" in result["IBM"].columns


@pytest.mark.slow
class TestFetchMetrics:
    def test_returns_dataframe(self):
        df = fetch_metrics(["IBM"])
        assert isinstance(df, pd.DataFrame)
        assert "IBM" in df.index

    def test_expected_columns(self):
        df = fetch_metrics(["IBM"])
        for col in ("Market Cap", "P/E Ratio", "Dividend Yield", "Beta", "Total Revenue"):
            assert col in df.columns


class TestPlotting:
    """Plot functions should return Plotly Figure objects."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Market Cap": [100.0, 200.0],
                "P/E Ratio": [25.0, 30.0],
                "Dividend Yield": [1.5, 0.8],
                "Beta": [1.1, 1.3],
                "Total Revenue": [50.0, 80.0],
            },
            index=["AAA", "BBB"],
        )

    @pytest.fixture
    def sample_histories(self) -> dict[str, pd.DataFrame]:
        import numpy as np

        idx = pd.date_range("2024-01-01", periods=30)
        return {
            "AAA": pd.DataFrame({"Close": np.random.default_rng(0).random(30) * 100}, index=idx),
        }

    def test_plot_stock_trends(self, sample_histories):
        fig = plot_stock_trends(sample_histories)
        assert isinstance(fig, go.Figure)

    def test_plot_metric_comparison(self, sample_df):
        fig = plot_metric_comparison(sample_df, "Market Cap")
        assert isinstance(fig, go.Figure)

    def test_plot_metrics_radar(self, sample_df):
        fig = plot_metrics_radar(sample_df)
        assert isinstance(fig, go.Figure)
