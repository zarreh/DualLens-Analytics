# Logging

DualLens Analytics uses Python's built-in `logging` module with a centralized
configuration function.

## Setup

Logging is configured once at application startup via
`duallens_analytics.configure_logging()`:

```python
from duallens_analytics import configure_logging

configure_logging(level="INFO")
```

### Default format

```
%(asctime)s | %(name)-35s | %(levelname)-8s | %(message)s
```

Example output:

```
2025-01-15 10:23:45,123 | duallens_analytics.config          | INFO     | Loading .env from /path/to/.env
2025-01-15 10:23:45,456 | duallens_analytics.vector_store    | INFO     | ChromaDB collection loaded – 142 documents
```

## Per-Module Loggers

Every module creates its own logger:

```python
import logging
logger = logging.getLogger(__name__)
```

This produces a hierarchy under `duallens_analytics.*`, so you can fine-tune
verbosity per module:

```python
logging.getLogger("duallens_analytics.financial").setLevel(logging.WARNING)
```

## What Gets Logged

| Module | Key Events |
|--------|-----------|
| `config` | `.env` load, Hydra config resolution, Settings creation |
| `data_loader` | ZIP extraction, PDF discovery, chunk counts |
| `vector_store` | Collection build/load, document counts |
| `financial` | Stock data fetch, metrics fetch, chart generation |
| `rag` | Question received, context length, answer length |
| `evaluation` | Judge prompt dispatch, score parsing |
| `ranking` | Ranking prompt dispatch |
| `report` | Report generation |
| `app` | Settings init, vector store init, tab rendering |
| `cli` | Config resolution output |

## Disabling Noisy Libraries

Third-party libraries (e.g., `httpx`, `chromadb`) can be silenced:

```python
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
```
