# Contributing to VeriLinkOS AI Verify Plugin

Thank you for your interest in contributing to the VeriLinkOS AI Verify Plugin! We welcome contributions from the community to help make AI governance more robust and accessible.

## 📜 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. We strive to maintain a welcoming, inclusive, and harassment-free environment for everyone.

## 🛠️ Development Setup

To start contributing, you'll need to set up your local development environment.

### 1. Clone the Repository
```bash
git clone https://github.com/rajinderjhol/verilink-aiverify-plugin.git
cd verilink-aiverify-plugin
```

### 2. Create a Virtual Environment
We recommend using a virtual environment to manage dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
Install the package in editable mode with development dependencies:
```bash
pip install -e ".[dev]"
```
*Note: If `[dev]` extras are not yet defined in `setup.py`, install `pytest` and `pytest-asyncio` manually.*

## 🧪 Testing

Before submitting any changes, ensure that all tests pass. This project uses `pytest` for testing.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v
```

If you add new features, please include corresponding test cases in the `tests/` directory.

## 🌿 Branching Strategy

1.  **Fork** the repository.
2.  Create a new **feature branch** from `main` (e.g., `feature/add-new-governance-rule`).
3.  Make your changes and commit them with descriptive messages.
4.  Push your branch to your fork.
5.  Open a **Pull Request** against the `main` branch of the original repository.

### Commit Messages

We follow Conventional Commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Testing improvements
- `chore:` Maintenance tasks

Example: `feat: add predictive enforcement capability`

## 📝 Coding Standards

- Follow PEP 8 for Python code style.
- Use type hints where possible to improve code clarity.
- Ensure all new functions and classes have appropriate docstrings.
- Keep your pull requests focused. If you have multiple unrelated changes, please submit them as separate PRs.

## 🐛 Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub. When reporting a bug, include:
- A clear description of the issue.
- Steps to reproduce the behavior.
- Expected vs. actual results.
- Your environment details (Python version, OS, etc.).

## 🚀 Submission Process

Once your Pull Request is submitted:
1.  CI tests will automatically run.
2.  A maintainer will review your changes.
3.  You may be asked to make some adjustments based on feedback.
4.  Once approved, your changes will be merged into `main`.

### Pull Request Checklist

Before submitting, please ensure:
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Code is formatted (`ruff format .`)
- [ ] No linting errors (`ruff check .`)
- [ ] Type hints added (`mypy verilink_plugin/`)
- [ ] Documentation is updated
- [ ] Commit messages follow conventions

## 📚 Additional Resources
- README - Project overview
- License - Apache 2.0
- PyPI - Package page

---
**Thank you for contributing!** ❤️