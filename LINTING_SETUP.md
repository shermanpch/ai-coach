# Pre-commit Linting Setup with Ruff

This project now uses **ruff** for linting and formatting Python code with **pre-commit** hooks for automated enforcement.

## What's Configured

### Ruff Configuration (`pyproject.toml`)
- **Linting**: Pyflakes, pycodestyle, isort, flake8-bugbear, flake8-comprehensions, pyupgrade
- **Formatting**: Black-compatible formatting with 88 character line length
- **Target**: Python 3.10+ compatibility
- **Auto-fix**: Enabled for all fixable rules

### Pre-commit Hooks (`.pre-commit-config.yaml`)
- **Code quality**: Trailing whitespace, end-of-file fixes, YAML validation
- **Security**: Large file checks, merge conflict detection
- **Python**: Debug statement detection, ruff linting and formatting

## Installation

The setup is already installed! But for new contributors:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Usage

### Automatic (Recommended)
Pre-commit hooks run automatically when you commit:
```bash
git add .
git commit -m "Your commit message"
# Hooks run automatically and may modify files
# If files are modified, you'll need to add and commit again
```

### Manual Testing
Run hooks on all files:
```bash
pre-commit run --all-files
```

Run only ruff:
```bash
ruff check .
ruff format .
```

## Configuration Details

- **Line length**: 88 characters (Black standard)
- **Quote style**: Double quotes
- **Import sorting**: isort with `src` as known first-party
- **Excludes**: Common directories like `.git`, `node_modules`, `catboost_info`, etc.

The setup provides a good balance of code quality enforcement while being practical for data science workflows.
