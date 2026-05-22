import asyncio
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage
from agents.orchestrator import build_orchestrator

graph = build_orchestrator()


async def main():
    print("========================================")
    print("JAI 2.0 Orchestrator Offline Terminal")
    print("========================================")
    print("Type 'exit' or 'quit' to stop.\n")

    context = {
        "user_id": "terminal_user",
        "tenant_id": "zerostic.com",
        "thread_id": "main-session",
    }

    while True:
        try:
            user_input = input("User: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break

            print("JAI is thinking...")
            result = await graph.ainvoke(
                {
                    "messages": [HumanMessage(content=user_input)],
                    "user_id": context["user_id"],
                    "tenant_id": context["tenant_id"],
                },
                config={"configurable": context},
            )
            print(f"\nJAI: {result['messages'][-1].content}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[ERROR] {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())
