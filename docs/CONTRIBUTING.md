# Contributing

Thank you for your interest in contributing to GML Infrastructure! This guide will help you get started.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/gml-infrastructure.git
   cd gml-infrastructure
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start development services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the development server**
   ```bash
   cd src
   python -m uvicorn gml.api.main:app --reload
   ```

## Commit Guidelines

Follow conventional commit format for clear and consistent commit messages:

- **feat**: new feature
- **fix**: bug fix
- **docs**: documentation
- **test**: add tests
- **refactor**: code refactor

**Example:**
```bash
git commit -m "feat: add message queue endpoint"
```

More examples:
```bash
git commit -m "fix: resolve agent registration duplicate error"
git commit -m "docs: update API documentation"
git commit -m "test: add integration tests for memory endpoints"
git commit -m "refactor: simplify agent service logic"
```

## Testing

All new features must include tests. Run tests with:

```bash
pytest tests/ -v --cov=src/gml
```

Run specific test suites:
```bash
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only
pytest tests/unit/test_agent_service.py -v  # Specific test file
```

Maintain test coverage above 80%.

## Code Style

Before submitting code, ensure it follows the project's style guidelines:

**Black formatting:**
```bash
black src/
```

**Import sorting:**
```bash
isort src/
```

**Type checking:**
```bash
mypy src/gml/
```

**Linting:**
```bash
pylint src/gml/
```

You can also use the Makefile shortcuts:
```bash
make format  # Runs black and isort
make lint    # Runs all linting tools
```

## Pull Request Process

1. **Fork repo** - Fork the repository to your GitHub account

2. **Create feature branch** - Create a branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

3. **Commit changes** - Make your changes and commit using the commit guidelines:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push and create PR** - Push your branch and create a Pull Request:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub with a clear description of your changes.

5. **Wait for review** - Maintainers will review your PR. Address any feedback and ensure all CI checks pass.

## Code of Conduct

Be respectful and inclusive. We welcome contributions from everyone regardless of background, experience level, or identity. Treat all contributors with respect and kindness.

## Additional Resources

- [Project Documentation](docs/README.md)
- [API Documentation](http://localhost:8000/api/docs)
- [Database Schema](src/gml/db/DATABASE.md)

## Questions?

If you have questions or need help, please:
- Open a GitHub Discussion
- Create an issue with the `question` label
- Reach out to maintainers

Thank you for contributing! 🎉
