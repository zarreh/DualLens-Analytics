# Contributing

## Development Setup

```bash
git clone <repo-url>
cd project_1_DualLens_Analytics
make install   # installs all dependency groups
```

## Code Quality

### Linting

```bash
make lint       # check for issues
make lint-fix   # auto-fix what's possible
```

### Formatting

```bash
make format        # apply formatting
make format-check  # check without modifying
```

### All checks at once

```bash
make check   # lint + format-check + tests
```

## Branching

1. Create a feature branch from `main`.
2. Make changes, ensuring `make check` passes.
3. Open a pull request with a clear description.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) via **Ruff**.
- Use type hints for function signatures.
- Write Google-style docstrings for public functions.
- Keep modules focused on a single responsibility.
