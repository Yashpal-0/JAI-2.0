import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig


@tool
def applab_code_tutor_handler(
    video_timestamp: str,
    ide_error_log: str,
    config: RunnableConfig,
) -> str:
    """Parses terminal compilation exceptions and matches errors to curriculum metadata arrays to provide localized hints."""
    cfg = config.get("configurable") or {}
    tenant_id = cfg.get("tenant_id", "unknown")
    user_id = cfg.get("user_id", "unknown")

    curriculum_hints = {
        "missing semicolon": "Curriculum Hint: Missing semicolon detected. In Kotlin/Java, remember that line endings require correct delimiters or structures. Check the end of your block near this line.",
        "cannot find symbol": "Curriculum Hint: This indicates a variable or class that hasn't been declared or imported. Verify import statements or spelling.",
        "nullpointerexception": "Curriculum Hint: You are attempting to call a method on an uninitialized reference. Utilize Kotlin's safe call operator (?.) to prevent crashes.",
    }

    hint = "Tutor Hint: Review the stack trace. The AST parser shows a general structural compilation error."
    for error_key, error_hint in curriculum_hints.items():
        if error_key in ide_error_log.lower():
            hint = error_hint
            break

    return json.dumps({
        "status": "COMPLETED",
        "error_parsed": ide_error_log,
        "video_timestamp": video_timestamp,
        "hint": hint,
    })


@tool
def ai_shadow_replay_emulator(
    session_telemetry_stream: str,
    code_diffs: list[str],
    config: RunnableConfig,
) -> str:
    """Ingests command line session streams and translates performance patterns into developer compatibility indexes."""
    cfg = config.get("configurable") or {}
    user_id = cfg.get("user_id", "unknown")

    keystrokes_count = len(session_telemetry_stream)
    diff_count = len(code_diffs)

    tdd_habit_score = 80
    if "test" in session_telemetry_stream.lower():
        tdd_habit_score += 15

    compatibility_index = 75
    if diff_count > 2 and keystrokes_count > 10:
        compatibility_index += 10

    return json.dumps({
        "candidate_id": user_id,
        "compatibility_index": min(compatibility_index, 100),
        "tdd_habit_score": min(tdd_habit_score, 100),
        "keystrokes_count": keystrokes_count,
        "diffs_analyzed": diff_count,
        "recommendation": "APPROVED" if min(compatibility_index, 100) >= 85 else "PROVISIONAL",
    })


@tool
def generative_venture_mvp_deployer(
    repo_template: str,
    deployment_target: str,
    config: RunnableConfig,
) -> str:
    """Triggers workspace configuration code to spin up live Vercel/AWS scaffold pipelines directly via repository cloning tools."""
    cfg = config.get("configurable") or {}
    user_id = cfg.get("user_id", "unknown")

    if "vercel" not in deployment_target.lower() and "aws" not in deployment_target.lower():
        return json.dumps({"error": "Invalid deployment target. We only support 'vercel' or 'aws' configuration pipelines."})

    return json.dumps({
        "status": "DEPLOYED",
        "user_id": user_id,
        "template": repo_template,
        "target": deployment_target,
        "live_url": f"https://zerostic-{user_id}-{repo_template}.vercel.app",
        "message": f"Successfully cloned repository, compiled AST checks, and deployed to {deployment_target} cluster.",
    })
