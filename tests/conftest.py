import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client():
    """Create a test client that uses the actual database configuration"""
    with TestClient(app, headers={}, cookies={}) as test_client:
        yield test_client
    # """Create a test client with minimal setup"""
    # return TestClient(app)
