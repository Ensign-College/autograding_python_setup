#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests with coverage
python -m pytest tests/ -v --cov=central_setup --cov-report=term-missing

# Deactivate virtual environment if activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
