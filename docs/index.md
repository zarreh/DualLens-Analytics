# DualLens Analytics

**RAG-Powered Investment Analysis Platform**

DualLens Analytics combines real-time financial data with AI-initiative knowledge
bases to provide a dual-lens view of public companies. It merges **quantitative
stock metrics** (via Yahoo Finance) with **qualitative AI-strategy insights**
extracted from PDF reports using a Retrieval-Augmented Generation (RAG) pipeline.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Interactive Dashboard** | Plotly charts for stock trends, financial metrics, and radar comparisons |
| **AI Q&A** | Ask natural-language questions about company AI initiatives |
| **Company Comparison** | Side-by-side radar charts of financial metrics |
| **Composite Rankings** | LLM-generated rankings combining financial health and AI strategy |
| **RAG Evaluation** | LLM-as-Judge scoring for groundedness and relevance |
| **Downloadable Reports** | Markdown reports summarizing analysis sessions |

## Technology Stack

- **LLM**: OpenAI `gpt-4o-mini` via LangChain
- **Embeddings**: `text-embedding-ada-002` → ChromaDB vector store
- **Financial Data**: Yahoo Finance (`yfinance`)
- **Frontend**: Streamlit (6-tab layout)
- **Configuration**: Hydra / OmegaConf + `.env` for secrets
- **Package Management**: Poetry
- **Quality**: Ruff (lint/format), pytest (36+ unit tests)

## Quick Links

- [Installation](getting-started/installation.md)
- [Configuration](getting-started/configuration.md)
- [Architecture Overview](architecture/overview.md)
- [API Reference](api/config.md)
