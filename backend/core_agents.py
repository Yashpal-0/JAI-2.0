from agents import Agent
from config import OPENROUTER_MODEL
from tools.pm_tools import autonomous_project_scoping, project_time_machine_simulator
from tools.dev_tools import applab_code_tutor_handler, ai_shadow_replay_emulator, generative_venture_mvp_deployer
from tools.analytics_tools import (
    fno_bazar_market_trigger_watcher,
    good_morning_alarm_telemetry_parser,
    frustration_analytics_collector,
    synthetic_user_persona_matrix,
    cross_ecosystem_context_weaver
)

# 1. Product Manager Agent
pm_agent = Agent(
    name="PM_Agent",
    model=OPENROUTER_MODEL,
    instructions="""
    You are the Zerostic Product Manager Agent. You reside on pm.zerostic.com.
    You handle project scoping, PRD generation, and team matchmaking analytics.
    IMPORTANT: You must maintain strict tenant isolation. Never leak project details to cross-tenant users.
    Use the contextual `user_id` and `tenant_id` to strictly limit data operations.
    """,
    tools=[autonomous_project_scoping, project_time_machine_simulator]
)

# 2. Developer Agent
developer_agent = Agent(
    name="Developer_Agent",
    model=OPENROUTER_MODEL,
    instructions="""
    You are the Zerostic Developer Agent. You reside on dev.zerostic.com.
    You guide freelancers through the AppLab sandboxed IDE, parse compilation logs, and deploy MVPs.
    IMPORTANT: You must maintain strict tenant isolation. Never leak codebase access or logs to unauthorized users.
    """,
    tools=[applab_code_tutor_handler, ai_shadow_replay_emulator, generative_venture_mvp_deployer]
)

# 3. Analytics & Data Weaver Agent
analytics_agent = Agent(
    name="Analytics_Agent",
    model=OPENROUTER_MODEL,
    instructions="""
    You are the Analytics and Telemetry Agent.
    You monitor FnO Bazar triggers, Good Morning Alarm telemetry, and Frustration analytics.
    IMPORTANT: Data routing must strictly enforce user_id constraints to prevent leaking one website's user data to another.
    """,
    tools=[
        fno_bazar_market_trigger_watcher,
        good_morning_alarm_telemetry_parser,
        frustration_analytics_collector,
        synthetic_user_persona_matrix,
        cross_ecosystem_context_weaver
    ]
)

# 4. Core Orchestrator (JAI 2.0 Router)
orchestrator_agent = Agent(
    name="JAI_Orchestrator",
    model=OPENROUTER_MODEL,
    instructions="""
    You are JAI 2.0, the central Orchestrator for Zerostic's Decentralized Marketplace.
    Your job is to route user intents to the appropriate specialized sub-agent.
    - If the user needs scoping, project estimation, or team simulation, route them to PM_Agent.
    - If the user needs code help, evaluation, or MVP deployment, route them to Developer_Agent.
    - If the user mentions market triggers, telemetry, or cross-ecosystem analytics, route them to Analytics_Agent.
    
    CRITICAL SECURITY MANDATE:
    You must enforce strict tenant isolation. When passing context, verify the `tenant_id` and `user_id`. Never leak one website's user data to another website's user. Protect the perimeter at all costs.
    """,
    handoffs=[pm_agent, developer_agent, analytics_agent]
)
