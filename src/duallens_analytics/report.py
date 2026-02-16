"""Generate a downloadable Markdown report summarising the analysis.

The report includes:

- The list of analysed companies.
- A formatted financial-metrics table.
- The AI-initiative composite ranking (if generated).
- The full Q&A chat log from the session.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import pandas as pd

logger = logging.getLogger(__name__)


def generate_report(
    companies: list[str],
    metrics_df: pd.DataFrame,
    ranking_text: str,
    chat_history: list[dict] | None = None,
) -> str:
    """Compile session artefacts into a Markdown report string.

    Args:
        companies: Ticker symbols included in the analysis.
        metrics_df: Financial-metrics DataFrame rendered via
            :meth:`~pandas.DataFrame.to_markdown`.
        ranking_text: Raw LLM ranking output.  Pass an empty string if
            no ranking has been generated yet.
        chat_history: Optional list of ``{"role": ..., "content": ...}``
            dicts from the AI Q&A session.

    Returns:
        A complete Markdown document ready for download.
    """
    logger.info("Generating report for %s", companies)
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "# DualLens Analytics – Investment Report",
        f"_Generated on {now}_\n",
        "## Companies Analysed",
        ", ".join(companies),
        "",
        "## Financial Metrics",
        metrics_df.to_markdown(),
        "",
        "## AI-Initiative Ranking",
        ranking_text if ranking_text else "_Not yet generated._",
        "",
    ]

    if chat_history:
        lines.append("## Q&A Log")
        for msg in chat_history:
            role = msg.get("role", "user").capitalize()
            lines.append(f"**{role}:** {msg['content']}\n")

    lines.append("\n---\n_Report produced by DualLens Analytics v0.1.0_")
    return "\n".join(lines)
