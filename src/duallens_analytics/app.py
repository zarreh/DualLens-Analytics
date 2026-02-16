"""DualLens Analytics – Streamlit application.

This module is the main entry-point for the interactive web UI.  It
orchestrates four tabs:

1. **Dashboard** – stock trends, financial metrics, and radar charts.
2. **AI Q&A** – chat interface backed by the RAG pipeline.
3. **Compare** – side-by-side company comparison.
4. **Rankings** – LLM-generated composite investment rankings.

Run with::

    poetry run streamlit run src/duallens_analytics/app.py
"""

from __future__ import annotations

import logging

import streamlit as st

from duallens_analytics import configure_logging
from duallens_analytics.config import (
    Settings,
    load_settings,
)
from duallens_analytics.financial import (
    fetch_metrics,
    fetch_stock_history,
    plot_metric_comparison,
    plot_metrics_radar,
    plot_stock_trends,
)
from duallens_analytics.rag import query_rag
from duallens_analytics.ranking import rank_companies
from duallens_analytics.vector_store import get_or_create_vector_store, get_retriever

logger = logging.getLogger(__name__)

# Activate logging before anything else
configure_logging()

# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DualLens Analytics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

_DISCLAIMER = (
    "⚠️ **Disclaimer:** This application is a **demonstration / educational "
    "prototype** only. The financial data shown may be outdated or inaccurate. "
    "Nothing here constitutes financial advice. **Do not** base any investment "
    "or financial decision on this analysis."
)


# ── helpers: cached loaders ────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading settings …")
def _load_settings() -> Settings:
    """Load and cache application settings.

    Settings are loaded once per Streamlit session and cached via
    :func:`st.cache_resource`.  API credentials are pushed into
    ``os.environ`` so that LangChain can discover them.

    Returns:
        A fully populated :class:`~duallens_analytics.config.Settings`.
    """
    logger.info("Initialising application settings")
    settings = load_settings()
    settings.apply_env()
    logger.info("Settings loaded (model=%s, companies=%s)", settings.model, settings.companies)
    return settings


@st.cache_resource(show_spinner="Loading vector store …")
def _init_vector_store(_settings: Settings):
    """Initialise or load the ChromaDB vector store and retriever.

    On the **first run** PDFs are extracted, chunked, embedded and
    persisted.  On subsequent runs the persisted store is loaded
    directly — no re-embedding required.

    Args:
        _settings: Application settings (prefixed with ``_`` so
            that Streamlit does not hash the object).

    Returns:
        A ``(store, retriever)`` tuple.
    """
    store = get_or_create_vector_store(_settings)
    retriever = get_retriever(store, k=_settings.retriever_k, search_type=_settings.search_type)
    return store, retriever


@st.cache_data(show_spinner="Fetching stock data …", ttl=3600)
def _fetch_stock(symbols: tuple[str, ...]):
    """Fetch and cache stock price history for the given symbols.

    Results are cached for 1 hour (``ttl=3600``).

    Args:
        symbols: Sorted tuple of ticker symbols (tuple for hashability).

    Returns:
        See :func:`~duallens_analytics.financial.fetch_stock_history`.
    """
    return fetch_stock_history(list(symbols))


@st.cache_data(show_spinner="Fetching financial metrics …", ttl=3600)
def _fetch_metrics(symbols: tuple[str, ...]):
    """Fetch and cache financial metrics for the given symbols.

    Results are cached for 1 hour (``ttl=3600``).

    Args:
        symbols: Sorted tuple of ticker symbols.

    Returns:
        See :func:`~duallens_analytics.financial.fetch_metrics`.
    """
    return fetch_metrics(list(symbols))


# ── sidebar ────────────────────────────────────────────────────────────────
def _sidebar(settings: Settings) -> list[str]:
    """Render the sidebar and return the list of selected companies.

    Displays the project logo, title, company multi-select widget,
    and a footer.  Calls :func:`st.stop` if no company is selected.

    Args:
        settings: Application settings providing the default company
            list.

    Returns:
        A list of selected ticker symbols.
    """
    with st.sidebar:
        st.image(
            "https://img.icons8.com/color/96/combo-chart.png",
            width=64,
        )
        st.title("DualLens Analytics")
        st.caption("RAG-powered investment analysis")

        selected = st.multiselect(
            "Companies to analyse",
            options=settings.companies,
            default=settings.companies,
        )
        if not selected:
            st.warning("Pick at least one company.")
            st.stop()

        st.divider()
        st.markdown("Built with **LangChain** · **ChromaDB** · **YFinance** · **Streamlit**")
        st.divider()
        st.warning(_DISCLAIMER)
    return selected


# ── Tab: Financial Dashboard ───────────────────────────────────────────────
def _tab_dashboard(companies: list[str], settings: Settings) -> None:
    """Render the Financial Dashboard tab.

    Shows stock price trends (line chart), a financial-metrics table,
    a single-metric bar chart, and a radar chart.

    Args:
        companies: Currently selected ticker symbols.
        settings: Application settings (used for metric selection).
    """
    st.header("📊 Financial Dashboard")

    symbols = tuple(sorted(companies))
    histories = _fetch_stock(symbols)
    metrics_df = _fetch_metrics(symbols)

    st.subheader("Stock Price Trends")
    st.plotly_chart(plot_stock_trends(histories), width="stretch", key="dash_stock")

    st.subheader("Key Financial Metrics")
    st.dataframe(metrics_df.style.format("{:,.2f}"), width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox("Metric to compare", settings.financial_metrics)
        st.plotly_chart(
            plot_metric_comparison(metrics_df, metric),
            width="stretch",
            key="dash_bar",
        )
    with col2:
        st.plotly_chart(plot_metrics_radar(metrics_df), width="stretch", key="dash_radar")


# ── Tab: RAG Q&A ──────────────────────────────────────────────────────────
def _tab_rag(settings: Settings, retriever) -> None:
    """Render the AI Initiative Q&A tab.

    Provides a chat interface where user questions are answered by the
    RAG pipeline.  Chat history is persisted in
    ``st.session_state.chat_history``.

    Args:
        settings: Application settings forwarded to
            :func:`~duallens_analytics.rag.query_rag`.
        retriever: LangChain retriever over the vector store.
    """
    st.header("🤖 AI Initiative Q&A")
    st.caption(
        "Ask anything about the AI initiatives of the analysed companies. "
        "Answers are grounded in the uploaded PDF knowledge base."
    )

    # Chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Render past messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # New user input
    if question := st.chat_input("e.g. What AI projects is NVDA working on?"):
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking …"):
                answer, sources = query_rag(question, retriever, settings)
            st.markdown(answer)

            with st.expander("📄 Retrieved context snippets"):
                for i, src in enumerate(sources, 1):
                    st.markdown(f"**Chunk {i}:** {src[:300]}…")

        st.session_state.chat_history.append({"role": "assistant", "content": answer})


# ── Tab: Comparison ────────────────────────────────────────────────────────
def _tab_compare(companies: list[str], settings: Settings, retriever) -> None:
    """Render the Side-by-Side Comparison tab.

    Allows the user to pick two companies, view their financial metrics
    on a radar chart, and read LLM-generated AI-initiative summaries.

    Args:
        companies: Currently selected ticker symbols.
        settings: Application settings.
        retriever: LangChain retriever for generating AI summaries.
    """
    st.header("⚖️ Side-by-Side Comparison")

    if len(companies) < 2:
        st.info("Select at least 2 companies for comparison.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        comp_a = st.selectbox("Company A", companies, index=0)
    with col_b:
        comp_b = st.selectbox("Company B", companies, index=min(1, len(companies) - 1))

    if comp_a == comp_b:
        st.warning("Pick two different companies.")
        return

    symbols = tuple(sorted([comp_a, comp_b]))
    metrics_df = _fetch_metrics(symbols)
    st.subheader("Financial Metrics")
    st.dataframe(metrics_df.style.format("{:,.2f}"), width="stretch")
    st.plotly_chart(plot_metrics_radar(metrics_df), width="stretch", key="cmp_radar")

    st.subheader("AI Initiative Summary")
    c1, c2 = st.columns(2)
    for col, sym in [(c1, comp_a), (c2, comp_b)]:
        with col:
            with st.spinner(f"Summarising {sym} …"):
                summary, _ = query_rag(
                    f"Provide a concise summary of the AI initiatives and projects of {sym}.",
                    retriever,
                    settings,
                )
            st.markdown(f"### {sym}")
            st.markdown(summary)


# ── Tab: Rankings ──────────────────────────────────────────────────────────
def _tab_rankings(companies: list[str], settings: Settings, store) -> None:
    """Render the Investment Rankings tab.

    A button triggers the LLM to produce a composite ranking that
    blends financial health with AI-strategy strength.  The result is
    stored in ``st.session_state["ranking_text"]``.

    Args:
        companies: Currently selected ticker symbols.
        settings: Application settings.
        store: ChromaDB vector store (passed to
            :func:`~duallens_analytics.ranking.rank_companies`).
    """
    st.header("🏆 Investment Rankings")

    symbols = tuple(sorted(companies))
    metrics_df = _fetch_metrics(symbols)

    if st.button("Generate Rankings", type="primary"):
        with st.spinner("LLM is analysing financial data + AI initiatives …"):
            ranking_text = rank_companies(metrics_df, store, settings)
        st.session_state["ranking_text"] = ranking_text

    if "ranking_text" in st.session_state:
        st.markdown(st.session_state["ranking_text"])


# ── main ───────────────────────────────────────────────────────────────────
def main() -> None:
    """Application entry-point: load settings, initialise stores, render tabs."""
    logger.info("Starting DualLens Analytics")
    settings = _load_settings()
    store, retriever = _init_vector_store(settings)
    companies = _sidebar(settings)
    logger.info("Selected companies: %s", companies)

    tabs = st.tabs(
        [
            "📊 Dashboard",
            "🤖 AI Q&A",
            "⚖️ Compare",
            "🏆 Rankings",
        ]
    )

    with tabs[0]:
        _tab_dashboard(companies, settings)
    with tabs[1]:
        _tab_rag(settings, retriever)
    with tabs[2]:
        _tab_compare(companies, settings, retriever)
    with tabs[3]:
        _tab_rankings(companies, settings, store)


if __name__ == "__main__":
    main()
