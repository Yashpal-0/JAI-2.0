import json
import pytest


def test_applab_code_tutor_missing_semicolon():
    from tools.dev_tools import applab_code_tutor_handler
    config = {"configurable": {"tenant_id": "dev.zerostic.com", "user_id": "dev1"}}
    result = applab_code_tutor_handler.invoke(
        {"video_timestamp": "02:34", "ide_error_log": "missing semicolon at line 12"},
        config=config,
    )
    data = json.loads(result)
    assert data["status"] == "COMPLETED"
    assert "semicolon" in data["hint"].lower()


def test_ai_shadow_replay_emulator_approved():
    from tools.dev_tools import ai_shadow_replay_emulator
    config = {"configurable": {"tenant_id": "dev.zerostic.com", "user_id": "dev1"}}
    result = ai_shadow_replay_emulator.invoke(
        {"session_telemetry_stream": "test command run test", "code_diffs": ["diff1", "diff2", "diff3"]},
        config=config,
    )
    data = json.loads(result)
    assert "compatibility_index" in data
    assert data["compatibility_index"] <= 100


def test_generative_venture_mvp_deployer_invalid_target():
    from tools.dev_tools import generative_venture_mvp_deployer
    config = {"configurable": {"tenant_id": "dev.zerostic.com", "user_id": "dev1"}}
    result = generative_venture_mvp_deployer.invoke(
        {"repo_template": "nextjs-starter", "deployment_target": "heroku"},
        config=config,
    )
    data = json.loads(result)
    assert "error" in data
