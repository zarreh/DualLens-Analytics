"""Unit tests for duallens_analytics.evaluation."""

from __future__ import annotations

from duallens_analytics.evaluation import EvalResult


class TestEvalResult:
    def test_parse_score_and_justification(self):
        raw = "Score: 4\nJustification: The answer is well grounded."
        result = EvalResult(dimension="Groundedness", raw_response=raw)
        assert result.score == 4
        assert "well grounded" in result.justification

    def test_parse_missing_score(self):
        raw = "The answer looks fine."
        result = EvalResult(dimension="Relevance", raw_response=raw)
        assert result.score is None

    def test_parse_score_with_extra_text(self):
        raw = "Score: 5 out of 5\nJustification: Perfect answer."
        result = EvalResult(dimension="Groundedness", raw_response=raw)
        assert result.score == 5
