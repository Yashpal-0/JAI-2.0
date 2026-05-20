import os
import asyncio
from agents import Runner, set_trace_processors
from config import custom_openrouter_client, get_trace_processors
from core_agents import orchestrator_agent

async def main():
    # Inject LangSmith Tracing if configured
    trace_processors = get_trace_processors()
    if trace_processors:
        print("[INFO] LangSmith tracing enabled.")
        set_trace_processors(trace_processors)

    print("========================================")
    print("JAI 2.0 Orchestrator Offline Terminal")
    print("Type 'exit' or 'quit' to end the session.")
    print("Security constraint: Cross-tenant leakage protection is ACTIVE.")
    print("========================================\\n")
    
    # We maintain a mock context that enforces tenant boundaries
    context = {
        "user_id": "user_123",
        "tenant_id": "studio.zerostic.com",
        "role": "lead_client"
    }
    
    while True:
        try:
            user_input = input("\\nUser: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            print("JAI 2.0 is routing...")
            # We inject the custom OpenRouter client into the Runner
            result = await Runner.run(
                agent=orchestrator_agent, 
                input=user_input,
                client=custom_openrouter_client,
                context=context
            )
            
            print(f"\\nJAI: {result.final_output}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\\n[ERROR] Execution failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
