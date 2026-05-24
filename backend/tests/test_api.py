import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock
from fastapi.testclient import TestClient


def test_chat_invalid_tenant():
    import api
    client = TestClient(api.app)
    response = client.post("/chat", json={
        "message": "hello",
        "user_id": "test_user",
        "tenant_id": "evil.com",
        "thread_id": "test-thread-001",
    })
    assert response.status_code == 400
    assert "Invalid tenant_id" in response.json()["detail"]

