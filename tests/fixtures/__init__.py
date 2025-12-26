"""
Test fixtures for GML Infrastructure
"""

import pytest
from typing import Generator


@pytest.fixture
def mock_agent():
    """Mock agent for testing"""
    return {
        "id": "test-agent-1",
        "name": "Test Agent",
        "type": "worker",
        "status": "active"
    }


@pytest.fixture
def mock_task():
    """Mock task for testing"""
    return {
        "id": "test-task-1",
        "name": "Test Task",
        "type": "processing",
        "status": "pending"
    }
