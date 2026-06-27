import pytest
import asyncio

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_config():
    return {
        "api_key": "test_key",
        "agent_id": "test_agent",
        "organization_id": "test_org"
    }
