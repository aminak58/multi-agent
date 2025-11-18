"""Simple smoke tests to verify basic functionality."""

import pytest


def test_python_version():
    """Test Python version is 3.10+."""
    import sys

    assert sys.version_info >= (3, 10)


def test_imports():
    """Test that key modules can be imported."""
    try:
        import fastapi
        import pydantic
        import redis
        import httpx
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_pydantic_model():
    """Test basic Pydantic model creation."""
    from pydantic import BaseModel

    class TestModel(BaseModel):
        name: str
        value: int

    model = TestModel(name="test", value=42)
    assert model.name == "test"
    assert model.value == 42


def test_environment_variables():
    """Test environment variables can be set."""
    import os

    os.environ["TEST_VAR"] = "test_value"
    assert os.environ.get("TEST_VAR") == "test_value"
