# Contributing to Franklin Shifts

Thank you for your interest in contributing to Franklin Shifts!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/franklin-shifts.git
   cd franklin-shifts
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Development Workflow

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests

3. Run tests to ensure everything works:
   ```bash
   pytest tests/ -v
   ```

4. Format your code:
   ```bash
   make lint
   # or
   black src/ tests/
   ruff check src/ tests/ --fix
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

6. Push to your fork and create a pull request

## Code Style

- Follow PEP 8 (enforced by black and ruff)
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and modular

## Testing

- Add tests for all new functionality
- Maintain or improve code coverage
- Test with both synthetic and real data if possible

## Documentation

- Update README.md if adding new features
- Add inline comments for complex logic
- Update config examples if changing configuration

## Questions?

Open an issue or reach out to the maintainers.

