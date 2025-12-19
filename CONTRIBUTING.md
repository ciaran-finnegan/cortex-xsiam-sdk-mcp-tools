# Contributing

Thank you for your interest in contributing to the Cortex XSIAM SDK MCP Tools.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Run `ruff check .` before committing
- Run `mypy mcp_demisto_sdk` for type checking

### Testing

```bash
pytest tests/
```

### Adding New Tools

1. Add the tool definition to `TOOLS` list in `server.py`
2. Create a handler function `handle_<tool_name>`
3. Register the handler in the `handlers` dictionary
4. Add tests for the new tool

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Ensure all tests pass
4. Submit a PR with a clear description

## Reporting Issues

- Use the GitHub issue tracker
- Include reproduction steps
- Provide environment details (Python version, OS, demisto-sdk version)

## Licence

By contributing, you agree that your contributions will be licensed under the MIT License.

