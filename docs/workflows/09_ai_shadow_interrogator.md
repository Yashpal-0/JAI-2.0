# 09 AI-Shadow Interrogator & Code-Replay Emulator

## Context
To vet freelance developers before they are assigned to a PRD generated in Workflow 01, we require an automated vetting pipeline.

## Predictive Marketplace Design
Instead of manual technical interviews, we deploy an AI-driven "Shadow Interrogator".

### Data Requirements & Hooks
- `sandbox_telemetry_stream`: Keystrokes, execution errors, and file saves from an in-browser IDE (similar to AppLab infrastructure).
- `llm_evaluator_agent`: Autogen-based agent evaluating coding speed, test-driven-development habits, and problem-solving.

### Logic Flow
1. **Developer Applies:** Developer connects GitHub or enters the Zerostic Sandbox.
2. **Dynamic Challenge Generation:** Agent generates a custom, non-Googleable coding challenge based on the current PRD requirements.
3. **Telemetry Capture:** Sandbox captures AST changes and sends WebSockets to the `AI_Shadow_Evaluator`.
4. **Replay Emulator:** PM dashboard receives a scrubbed, accelerated replay of the developer's session accompanied by an AI-generated risk score.
