# Central Setup

[![Python Tests](https://github.com/YOUR_USERNAME/central_setup/actions/workflows/python-tests.yml/badge.svg)](https://github.com/YOUR_USERNAME/central_setup/actions/workflows/python-tests.yml)
[![Code Quality](https://github.com/YOUR_USERNAME/central_setup/actions/workflows/code-quality.yml/badge.svg)](https://github.com/YOUR_USERNAME/central_setup/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/central_setup/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/central_setup)

A Python package for handling central setup tasks for student code autograding.

## Features

- Runs tests against student code
- Sends results to an autograding API
- Handles token authentication for GitHub
- Includes comprehensive test suite

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The package supports configuration through environment variables:

- `AUTOGRADING_BASE_URL`: The base URL for the autograding API (defaults to `https://autograding-api-next.vercel.app/api/autograde`)
- `GITHUB_TOKEN`: GitHub authentication token (optional)

## Testing

Run the tests with:

```bash
./run_tests.sh
```

Or run with coverage:

```bash
./run_tests_with_coverage.sh
```

## Development

Before submitting a PR, make sure:

1. All tests pass
2. Code is formatted with Black
3. Imports are sorted with isort
4. No linting errors from flake8
