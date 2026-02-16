"""Unit tests for duallens_analytics.report."""

from __future__ import annotations

import pandas as pd
import pytest

from duallens_analytics.report import generate_report


class TestGenerateReport:
    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Market Cap": [100.0],
                "P/E Ratio": [25.0],
                "Dividend Yield": [1.5],
                "Beta": [1.1],
                "Total Revenue": [50.0],
            },
            index=["IBM"],
        )

    def test_returns_string(self, sample_df):
        md = generate_report(["IBM"], sample_df, "Ranking text")
        assert isinstance(md, str)

    def test_contains_title(self, sample_df):
        md = generate_report(["IBM"], sample_df, "Ranking text")
        assert "DualLens Analytics" in md

    def test_contains_company(self, sample_df):
        md = generate_report(["IBM"], sample_df, "Ranking text")
        assert "IBM" in md

    def test_contains_ranking(self, sample_df):
        md = generate_report(["IBM"], sample_df, "Ranking text")
        assert "Ranking text" in md

    def test_chat_history_included(self, sample_df):
        history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        md = generate_report(["IBM"], sample_df, "", history)
        assert "Q&A Log" in md
        assert "Hello" in md

    def test_empty_ranking(self, sample_df):
        md = generate_report(["IBM"], sample_df, "")
        assert "Not yet generated" in md
