#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Running black..."
black central_setup/ tests/ || exit 1

echo "Running isort..."
isort central_setup/ tests/ || exit 1

echo "Running flake8..."
flake8 central_setup/ tests/ || exit 1

echo "Running tests..."
python -m pytest tests/ -v --cov=central_setup --cov-report=term-missing || exit 1

echo "All checks passed!"

# Deactivate virtual environment if activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
