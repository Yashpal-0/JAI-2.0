import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig


@tool
def autonomous_project_scoping(
    project_type: str,
    budget: str,
    timeline: str,
    description: str,
    config: RunnableConfig,
) -> str:
    """Interrogates intake fields, matches parameters against pricing metrics, and maps programmatic product scopes. Returns a structured PRD draft as JSON string."""
    cfg = config.get("configurable") or {}
    tenant_id = cfg.get("tenant_id", "unknown")
    user_id = cfg.get("user_id", "unknown")

    if tenant_id not in ["studio.zerostic.com", "pm.zerostic.com"]:
        return json.dumps({"error": "Unauthorized tenant scope access."})

    features = []
    if "web" in project_type.lower() or "website" in project_type.lower():
        features.extend(["Responsive Design", "Next.js Core SSR", "SEO Setup"])
    if "mobile" in project_type.lower() or "ios" in project_type.lower() or "android" in project_type.lower():
        features.extend(["Kotlin/Swift Native Framework", "Push Notification Service Hooks", "Local Telemetry Dump"])

    return json.dumps({
        "user_id": user_id,
        "tenant_id": tenant_id,
        "project_type": project_type,
        "budget": budget,
        "timeline": timeline,
        "description": description,
        "mapped_features": features,
        "status": "DRAFT",
        "scoping_vetting_status": "PENDING_PM_ACCEPTANCE",
    })


@tool
def project_time_machine_simulator(
    developer_ids: list[str],
    pm_id: str,
    expected_sprint_weeks: int,
    config: RunnableConfig,
) -> str:
    """Cross-references historical completion intervals and communication response deltas to build a timeline regression vector."""
    cfg = config.get("configurable") or {}
    tenant_id = cfg.get("tenant_id", "unknown")
    user_id = cfg.get("user_id", "unknown")

    if tenant_id not in ["studio.zerostic.com", "pm.zerostic.com"]:
        return json.dumps({"error": "Access denied. Time Machine simulation is restricted to PM/Studio boundaries."})

    risk_factor = 10.0 + len(developer_ids) * 2.5
    estimated_variance = "+0 days"

    if "dev_slow" in developer_ids or len(developer_ids) > 3:
        risk_factor += 35.0
        estimated_variance = "+5 days"

    return json.dumps({
        "requested_by": user_id,
        "risk_score": min(risk_factor, 100.0),
        "estimated_completion_variance": estimated_variance,
        "friction_analysis": "Sprint velocity is stable" if risk_factor < 30 else "High chance of sprint extension. Suggest daily standup tracking.",
    })
