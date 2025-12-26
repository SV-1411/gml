# Pre-commit Hooks Setup Guide

This guide explains how to set up and use pre-commit hooks for GML Infrastructure.

## What are Pre-commit Hooks?

Pre-commit hooks automatically run code quality checks before you commit code. This ensures:
- Code is properly formatted
- Imports are sorted correctly
- Type checking passes
- Linting issues are caught
- Tests pass

## Installation

### Step 1: Install pre-commit

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Install pre-commit
pip install pre-commit
```

### Step 2: Install Git Hooks

```bash
# Install hooks into .git/hooks/
pre-commit install

# For commit messages (optional)
pre-commit install --hook-type commit-msg
```

This installs hooks that run automatically on `git commit`.

## Usage

### Automatic Execution

Hooks run automatically when you commit:

```bash
git add .
git commit -m "feat: add new feature"
# Pre-commit hooks run automatically here
```

If any hook fails, the commit is blocked. Fix the issues and commit again.

### Manual Execution

Run hooks manually on all files:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run a specific hook
pre-commit run black --all-files
pre-commit run isort --all-files
pre-commit run mypy --all-files
pre-commit run pylint --all-files
pre-commit run pytest --all-files
```

### Run on Staged Files Only

```bash
# Run hooks only on staged files (default behavior)
pre-commit run
```

## Configured Hooks

### 1. Black Formatter

**Purpose:** Automatically formats Python code to a consistent style.

**Configuration:**
- Line length: 100 characters
- Python version: 3.11
- Excludes: Migration files, generated code

**Manual run:**
```bash
pre-commit run black --all-files
# or
black src/ tests/
```

### 2. isort Import Sorting

**Purpose:** Sorts and organizes import statements.

**Configuration:**
- Profile: black (compatible with black formatter)
- Line length: 100 characters
- Excludes: Migration files

**Manual run:**
```bash
pre-commit run isort --all-files
# or
isort src/ tests/
```

### 3. mypy Type Checking

**Purpose:** Static type checking for Python code.

**Configuration:**
- Python version: 3.11
- Strict type checking enabled
- Excludes: Tests, migrations, examples

**Manual run:**
```bash
pre-commit run mypy --all-files
# or
mypy src/gml/
```

### 4. Pylint Linting

**Purpose:** Catches code quality issues and potential bugs.

**Configuration:**
- Max line length: 100
- Disabled warnings: docstrings, naming conventions
- Excludes: Tests, migrations, examples, venv

**Manual run:**
```bash
pre-commit run pylint --all-files
# or
pylint src/gml/
```

### 5. Pytest Unit Tests

**Purpose:** Runs unit tests before committing.

**Configuration:**
- Runs: `tests/unit/` directory
- Verbose output
- Short traceback format
- Always runs (not file-based)

**Manual run:**
```bash
pre-commit run pytest --all-files
# or
pytest tests/unit/ -v
```

## Excluded Files

The following are automatically excluded from hooks:

- `alembic/versions/*.py` - Auto-generated migration files
- `migrations/*.py` - Migration files
- `venv/`, `.venv/` - Virtual environments
- `.git/` - Git directory
- `.mypy_cache/`, `.pytest_cache/` - Cache directories
- `build/`, `dist/` - Build artifacts
- `node_modules/` - Node.js dependencies
- Coverage files

## Updating Hooks

Update hook versions:

```bash
# Update all hooks to latest versions
pre-commit autoupdate

# Update specific hook
pre-commit autoupdate --repo https://github.com/psf/black
```

## Skipping Hooks

**Skip all hooks for a commit:**
```bash
git commit --no-verify -m "WIP: skip hooks"
```

**Skip specific hook:**
```bash
SKIP=mypy git commit -m "feat: add feature"
```

**⚠️ Warning:** Only skip hooks when absolutely necessary (e.g., WIP commits).

## Troubleshooting

### Hooks Not Running

```bash
# Verify hooks are installed
ls -la .git/hooks/

# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Hook Fails on Cleanup

```bash
# Clear pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit install
```

### mypy Errors

```bash
# Install type stubs
pip install types-redis types-pyyaml

# Run mypy manually to see detailed errors
mypy src/gml/ --show-error-codes
```

### Pytest Fails

```bash
# Run pytest manually to see detailed output
pytest tests/unit/ -v --tb=long

# Check if database is running
docker-compose -f docker-compose.dev.yml ps
```

### Black/isort Conflicts

```bash
# Run isort first, then black
isort src/ tests/
black src/ tests/

# Or use pre-commit which runs them in correct order
pre-commit run --all-files
```

## Integration with CI/CD

Pre-commit hooks can also run in CI:

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit
on: [push, pull_request]
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - uses: pre-commit/action@v3.0.0
```

## Best Practices

1. **Run hooks before committing:**
   ```bash
   pre-commit run --all-files
   git add .
   git commit -m "feat: add feature"
   ```

2. **Fix issues immediately:**
   - Don't skip hooks unless absolutely necessary
   - Fix formatting/linting issues as they appear

3. **Keep hooks updated:**
   ```bash
   pre-commit autoupdate
   ```

4. **Use Makefile shortcuts:**
   ```bash
   make format  # Runs black and isort
   make lint    # Runs all linting tools
   ```

## Quick Reference

```bash
# Install
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Skip hooks (not recommended)
git commit --no-verify

# Uninstall
pre-commit uninstall
```

## Additional Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Pylint Documentation](https://pylint.readthedocs.io/)

