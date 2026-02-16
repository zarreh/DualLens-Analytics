"""Fetch financial data from Yahoo Finance and build Plotly visualisations.

This module provides two groups of functionality:

1. **Data fetching** – :func:`fetch_stock_history` and :func:`fetch_metrics`
   pull real-time stock prices and fundamental metrics from Yahoo Finance
   using the ``yfinance`` library.
2. **Charting** – :func:`plot_stock_trends`, :func:`plot_metric_comparison`,
   and :func:`plot_metrics_radar` return interactive Plotly figures ready
   to be rendered by Streamlit.
"""

from __future__ import annotations

import logging

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

from duallens_analytics.config import (  # defaults; overridden via Settings
    FINANCIAL_METRICS,
    STOCK_PERIOD,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stock price history
# ---------------------------------------------------------------------------
def fetch_stock_history(
    symbols: list[str],
    period: str = STOCK_PERIOD,
) -> dict[str, pd.DataFrame]:
    """Download OHLCV price history for each ticker symbol.

    Args:
        symbols: List of Yahoo-Finance ticker symbols
            (e.g. ``["GOOGL", "MSFT"]``).
        period: Look-back period accepted by :meth:`yfinance.Ticker.history`
            (e.g. ``"1y"``, ``"3y"``, ``"max"``).

    Returns:
        A dictionary mapping each symbol to a :class:`~pandas.DataFrame`
        with columns ``Open``, ``High``, ``Low``, ``Close``, ``Volume``
        and a ``DatetimeIndex``.
    """
    logger.info("Fetching stock history for %s (period=%s)", symbols, period)
    histories: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        logger.debug("Downloading history for %s", sym)
        ticker = yf.Ticker(sym)
        histories[sym] = ticker.history(period=period)
        logger.debug("%s: %d rows retrieved", sym, len(histories[sym]))
    return histories


def plot_stock_trends(histories: dict[str, pd.DataFrame]) -> go.Figure:
    """Build a Plotly line chart of closing prices for all companies.

    Args:
        histories: Mapping returned by :func:`fetch_stock_history`.

    Returns:
        A :class:`~plotly.graph_objects.Figure` with one trace per company.
    """
    fig = go.Figure()
    for sym, df in histories.items():
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name=sym))
    fig.update_layout(
        title="Stock Price Trends",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white",
        height=500,
    )
    return fig


# ---------------------------------------------------------------------------
# Financial metrics
# ---------------------------------------------------------------------------
def fetch_metrics(symbols: list[str]) -> pd.DataFrame:
    """Fetch key financial metrics and return a tidy DataFrame.

    The following metrics are retrieved per company:

    - **Market Cap** – scaled to billions (USD).
    - **P/E Ratio** – trailing price-to-earnings.
    - **Dividend Yield** – scaled to percentage.
    - **Beta** – volatility relative to the market.
    - **Total Revenue** – scaled to billions (USD).

    Args:
        symbols: List of Yahoo-Finance ticker symbols.

    Returns:
        A :class:`~pandas.DataFrame` indexed by symbol with one column
        per metric.  Values are human-readable (billions / percentages).
    """
    logger.info("Fetching financial metrics for %s", symbols)
    rows: dict[str, dict] = {}
    for sym in symbols:
        logger.debug("Fetching info for %s", sym)
        info = yf.Ticker(sym).info
        rows[sym] = {
            "Market Cap": info.get("marketCap", 0),
            "P/E Ratio": info.get("trailingPE", 0),
            "Dividend Yield": info.get("dividendYield", 0),
            "Beta": info.get("beta", 0),
            "Total Revenue": info.get("totalRevenue", 0),
        }
    df = pd.DataFrame(rows).T
    # Human-readable scaling
    df["Market Cap"] = df["Market Cap"] / 1e9
    df["Total Revenue"] = df["Total Revenue"] / 1e9
    df["Dividend Yield"] = df["Dividend Yield"] * 100
    return df


def plot_metric_comparison(df: pd.DataFrame, metric: str) -> go.Figure:
    """Create a bar chart comparing a single *metric* across companies.

    Args:
        df: Financial-metrics DataFrame as returned by
            :func:`fetch_metrics`.
        metric: Column name to plot (e.g. ``"Market Cap"``).

    Returns:
        A :class:`~plotly.graph_objects.Figure` bar chart.
    """
    fig = px.bar(
        df.reset_index(),
        x="index",
        y=metric,
        color="index",
        labels={"index": "Company", metric: metric},
        title=f"{metric} Comparison",
        template="plotly_white",
    )
    fig.update_layout(showlegend=False, height=400)
    return fig


def plot_metrics_radar(df: pd.DataFrame) -> go.Figure:
    """Build a radar (spider) chart overlaying normalised metrics.

    Each metric column is min–max normalised to the 0–1 range so that
    all axes share a common scale.

    Args:
        df: Financial-metrics DataFrame as returned by
            :func:`fetch_metrics`.

    Returns:
        A :class:`~plotly.graph_objects.Figure` with one polar trace per
        company.
    """
    # Normalise each column 0-1 for radar
    norm = (df - df.min()) / (df.max() - df.min() + 1e-9)
    fig = go.Figure()
    for sym in norm.index:
        fig.add_trace(
            go.Scatterpolar(
                r=[*norm.loc[sym].tolist(), norm.loc[sym].iloc[0]],
                theta=[*FINANCIAL_METRICS, FINANCIAL_METRICS[0]],
                fill="toself",
                name=sym,
            )
        )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Financial Metrics – Radar",
        template="plotly_white",
        height=500,
    )
    return fig
