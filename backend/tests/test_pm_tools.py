import json
import pytest


def test_autonomous_project_scoping_valid_tenant():
    from tools.pm_tools import autonomous_project_scoping
    config = {"configurable": {"tenant_id": "studio.zerostic.com", "user_id": "user1"}}
    result = autonomous_project_scoping.invoke(
        {"project_type": "web", "budget": "5000", "timeline": "4 weeks", "description": "Portfolio site"},
        config=config,
    )
    data = json.loads(result)
    assert data["tenant_id"] == "studio.zerostic.com"
    assert data["user_id"] == "user1"
    assert data["status"] == "DRAFT"
    assert "Responsive Design" in data["mapped_features"]


def test_autonomous_project_scoping_invalid_tenant():
    from tools.pm_tools import autonomous_project_scoping
    config = {"configurable": {"tenant_id": "evil.com", "user_id": "attacker"}}
    result = autonomous_project_scoping.invoke(
        {"project_type": "web", "budget": "1000", "timeline": "1 week", "description": "test"},
        config=config,
    )
    data = json.loads(result)
    assert "error" in data


def test_project_time_machine_simulator_valid():
    from tools.pm_tools import project_time_machine_simulator
    config = {"configurable": {"tenant_id": "studio.zerostic.com", "user_id": "pm1"}}
    result = project_time_machine_simulator.invoke(
        {"developer_ids": ["dev1", "dev2"], "pm_id": "pm1", "expected_sprint_weeks": 3},
        config=config,
    )
    data = json.loads(result)
    assert "risk_score" in data
    assert data["risk_score"] <= 100.0
