# Configuration

DualLens Analytics uses a **two-layer** configuration system:

1. **Secrets** – loaded from `.env` via `python-dotenv`
2. **Application parameters** – loaded from `conf/config.yaml` via Hydra / OmegaConf

---

## Environment Variables (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes | OpenAI-compatible API key |
| `OPENAI_API_BASE` | Yes | Base URL for the LLM endpoint |

```dotenv
API_KEY=gl-xxxxx
OPENAI_API_BASE=https://aibe.mygreatlearning.com/openai/v1
```

!!! warning
    Never commit `.env` to version control. It is listed in `.gitignore`.

---

## Hydra Config (`conf/config.yaml`)

The YAML file is divided into logical sections:

### LLM

```yaml
llm:
  model: gpt-4o-mini
  temperature: 0.3
  max_tokens: 1024
  top_p: 1.0
  frequency_penalty: 0.0
```

### Embedding

```yaml
embedding:
  model: text-embedding-ada-002
```

### Chunking

Controls how PDF documents are split before embedding:

```yaml
chunking:
  chunk_size: 1000
  chunk_overlap: 200
  encoding_name: cl100k_base
```

### Retriever

```yaml
retriever:
  k: 5
  search_type: similarity
```

### Vector Store

```yaml
vector_store:
  collection_name: ai_initiatives
```

### Companies & Financial

```yaml
companies:
  - Google
  - Microsoft
  - Amazon
  - Meta

stock:
  period: 1y

financial_metrics:
  - revenue
  - market_cap
  - total_debt
  - free_cash_flow
  - operating_income
```

---

## Overriding via CLI (Hydra)

Any config value can be overridden from the command line:

```bash
poetry run python -m duallens_analytics.cli llm.temperature=0.7 retriever.k=10
```

See the [Hydra documentation](https://hydra.cc/docs/intro/) for advanced
override syntax.
