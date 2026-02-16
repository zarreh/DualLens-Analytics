# Testing

## Running Tests

```bash
make test          # run all tests (skip slow)
make test-cov      # run with coverage report
```

### Slow tests

Tests that hit external APIs (Yahoo Finance, OpenAI) are marked with
`@pytest.mark.slow` and skipped by default. To include them:

```bash
poetry run pytest -m slow
poetry run pytest          # without the deselect filter
```

## Test Structure

```
tests/
├── __init__.py
├── test_config.py         # Settings, Hydra, path constants
├── test_data_loader.py    # ZIP extraction, PDF loading
├── test_evaluation.py     # EvalResult parsing
├── test_financial.py      # Chart generation + slow API tests
└── test_report.py         # Markdown report output
```

## Writing Tests

- Place tests in `tests/test_<module>.py`.
- Use `tmp_path` fixtures for file-system tests.
- Mark API-dependent tests:

```python
import pytest

@pytest.mark.slow
def test_live_api_call():
    ...
```

## Coverage

```bash
make test-cov
```

Generates a terminal coverage report. Aim for ≥ 80 % coverage on utility
modules (`config`, `data_loader`, `evaluation`, `report`).
