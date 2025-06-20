# Integration Tests

This directory contains integration tests for the AI Assistant Server.

## Setup

Install test dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

### Run all integration tests

```bash
pytest tests/integration
```

### Run tests with coverage

```bash
pytest tests/integration --cov=app
```

### Run a specific test

```bash
pytest tests/integration/test_message_routes.py::TestMessageRoutes::test_create_message
```

## Test Database

Tests use an in-memory SQLite database for isolation. No production data is affected.

## Structure

- `conftest.py`: Contains pytest fixtures for database and client setup
- `integration/`: Integration tests that test the API endpoints
  - `test_message_routes.py`: Tests for message-related endpoints

## Adding New Tests

Follow the existing patterns to add new integration tests:

1. Create a test class in the appropriate test file
2. Use the `client` fixture to make HTTP requests
3. Assert the expected responses and database state
