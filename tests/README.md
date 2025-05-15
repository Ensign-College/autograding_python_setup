# Central Setup Tests

This directory contains tests for the central_setup module.

## Running Tests

You can run the tests using pytest:

```bash
# From the project root directory
pytest
```

Or use the convenience script to run with coverage:

```bash
# From the project root directory
./run_tests.sh
```

## Test Structure

- `test_central_setup.py`: Main tests covering all functionality of the module
- `test_autograding_url.py`: Focused tests for the AUTOGRADING_BASE_URL environment variable

## Coverage Reports

The tests are configured to generate coverage reports. When using the `run_tests.sh` script, you'll see a coverage report in the terminal showing which lines of code were executed during the tests and which ones were missed.

## Dependencies

The testing requirements are included in the project's `requirements.txt` file. Make sure to install them before running the tests:

```bash
pip install -r requirements.txt
```
