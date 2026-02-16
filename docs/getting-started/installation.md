# Installation

## Prerequisites

- **Python 3.12+**
- **Poetry** (package manager)

## Steps

### 1. Clone the repository

```bash
git clone <repo-url>
cd project_1_DualLens_Analytics
```

### 2. Install dependencies

```bash
make install
# or manually:
poetry install --with dev,docs
```

### 3. Set up environment variables

Copy the example file and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env` with your OpenAI-compatible API key:

```dotenv
API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
```

### 4. Prepare data

Place company AI-initiative PDFs inside `data/ai_initiatives/` or provide
the ZIP archive at `data/ai_initiative_reports.zip`. The application extracts
and indexes them automatically on first run.

### 5. Run the application

```bash
make run
# or:
poetry run streamlit run src/duallens_analytics/app.py
```

The Streamlit app opens at [http://localhost:8510](http://localhost:8510).

## Optional: Build documentation

```bash
make docs       # build static site
make docs-serve # live-reload dev server
```
