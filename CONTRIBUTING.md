# Contributing to Sherly AI

First off, thank you for considering contributing to Sherly AI! It's people like you that make Sherly such a powerful and secure local orchestrator.

## 🤝 Code of Conduct
By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to the project maintainers.

## 🛠️ Getting Started

### 1. Fork and Clone
Fork the repository on GitHub and clone your fork locally:
```bash
git clone https://github.com/YOUR-USERNAME/sherly.git
cd sherly
```

### 2. Set Up the Environment
Create a virtual environment and install the required dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Pre-Commit Hooks
We use `pre-commit` to maintain code quality. Install it using:
```bash
pre-commit install
```
This ensures your code is formatted (with Ruff) before every commit.

## 🌿 Branching Strategy

- **`main`**: The primary, stable branch.
- **`dev`** or **`develop`**: Integration branch for upcoming releases.
- **Feature Branches**: Branch off `dev` using the format `feature/your-feature-name`.
- **Bugfix Branches**: Branch off `dev` using the format `bugfix/issue-description`.

## 💻 Coding Standards

- **Python Version**: 3.10+
- **Type Hinting**: All new functions must include type hints.
- **Docstrings**: We follow Google-style docstrings.
- **Linting**: Code must pass `ruff` validation.
- **UI Framework**: PySide6 is used for the desktop frontend. Ensure UI logic is decoupled from `sherly_core`.

## 🧪 Testing

Sherly relies heavily on tests to ensure the deterministic safety layers remain intact.

- Run the full test suite before submitting a PR:
  ```bash
  pytest tests/
  ```
- Any new features must include corresponding unit tests.
- Bug fixes should include regression tests to prevent the issue from reappearing.

## 📝 Pull Request Process

1. Ensure your branch is up-to-date with `dev`.
2. Push your changes to your fork.
3. Open a Pull Request against the `dev` branch.
4. Fill out the PR template completely.
5. Wait for CI checks to pass and a maintainer to review.

### PR Title Format
Please use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation updates
- `refactor:` for code restructuring without behavioral changes

Thank you for helping us bring agency back to the local development environment!
