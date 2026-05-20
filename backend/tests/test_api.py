import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock
from fastapi.testclient import TestClient


def test_chat_invalid_tenant():
    import api
    api.app.dependency_overrides[api.get_graph] = lambda: MagicMock()
    client = TestClient(api.app)
    response = client.post("/chat", json={
        "message": "hello",
        "user_id": "test_user",
        "tenant_id": "evil.com",
        "thread_id": "test-thread-001",
    })
    api.app.dependency_overrides.clear()
    assert response.status_code == 400
    assert "Invalid tenant_id" in response.json()["detail"]
