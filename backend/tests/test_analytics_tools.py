import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_fno_bazar_valid_asset():
    from tools.analytics_tools import fno_bazar_market_trigger_watcher
    config = {"configurable": {"tenant_id": "zerostic.com", "user_id": "user1"}}
    result = fno_bazar_market_trigger_watcher.invoke(
        {"intent_string": "alert when above 20000", "asset_symbol": "NIFTY", "threshold": 20000.0},
        config=config,
    )
    data = json.loads(result)
    assert data["asset_symbol"] == "NIFTY"
    assert data["status"] == "ACTIVE_WATCH"


def test_fno_bazar_invalid_asset():
    from tools.analytics_tools import fno_bazar_market_trigger_watcher
    config = {"configurable": {"tenant_id": "zerostic.com", "user_id": "user1"}}
    result = fno_bazar_market_trigger_watcher.invoke(
        {"intent_string": "alert", "asset_symbol": "DOGE", "threshold": 1.0},
        config=config,
    )
    data = json.loads(result)
    assert "error" in data


def test_cross_ecosystem_context_weaver_user_mismatch():
    from tools.analytics_tools import cross_ecosystem_context_weaver
    config = {"configurable": {"tenant_id": "zerostic.com", "user_id": "user_actual"}}
    result = cross_ecosystem_context_weaver.invoke(
        {"user_id": "user_different", "source_ecosystem": "fno_bazar", "trigger_event": "low sleep"},
        config=config,
    )
    data = json.loads(result)
    assert "error" in data


def test_cross_ecosystem_context_weaver_user_match():
    from tools.analytics_tools import cross_ecosystem_context_weaver
    config = {"configurable": {"tenant_id": "zerostic.com", "user_id": "user1"}}
    result = cross_ecosystem_context_weaver.invoke(
        {"user_id": "user1", "source_ecosystem": "fno_bazar", "trigger_event": "normal day"},
        config=config,
    )
    data = json.loads(result)
    assert data["integrity_checksum"] == "INTEGRITY_VERIFIED"
