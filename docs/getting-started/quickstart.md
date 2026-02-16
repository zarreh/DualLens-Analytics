# Quick Start

After [installing](installation.md) and [configuring](configuration.md) the project, follow
these steps to get a feel for the platform.

## 1. Launch the Streamlit app

```bash
make run
```

## 2. Explore the tabs

### Dashboard

Select one or more companies in the sidebar. The dashboard shows:

- Stock price trend (line chart)
- Financial metric comparison (bar chart)
- Metrics radar chart

### AI Q&A

Type a question such as:

> *What is Google's strategy for generative AI?*

The RAG pipeline retrieves relevant passages from the PDF knowledge base and
generates a grounded answer.

### Compare

Pick two or more companies and view their financial metrics side-by-side on
a radar chart.

### Rankings

Click **Generate Rankings** to get a composite score that blends financial
health with AI-strategy strength, powered by the LLM.

### Evaluation

After asking questions in the AI Q&A tab, switch to Evaluation to see
LLM-as-Judge scores for **groundedness** and **relevance**.

### Report

Generate and download a Markdown report summarizing the session's findings.

## 3. Run from the CLI

```bash
make hydra
# Override parameters:
poetry run python -m duallens_analytics.cli llm.temperature=0.5
```
