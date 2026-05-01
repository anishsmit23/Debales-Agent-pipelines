from __future__ import annotations

from dotenv import load_dotenv

from agent.graph import app

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:  # pragma: no cover
    Console = None
    Panel = None


def ask(query: str) -> dict:
    initial_state = {
        "query": query,
        "route": None,
        "rag_context": None,
        "serp_context": None,
        "context": None,
        "no_context": False,
        "answer": None,
        "sources": [],
    }
    return app.invoke(initial_state)


def run_cli() -> None:
    load_dotenv()
    console = Console() if Console else None

    if console:
        console.print(Panel.fit("Debales AI Assistant\nType 'exit' to quit."))
    else:
        print("Debales AI Assistant")
        print("Type 'exit' to quit.")

    while True:
        query = input("\nYou: ").strip()
        if query.lower() in {"exit", "quit", "q"}:
            break
        if not query:
            continue

        try:
            result = ask(query)
        except Exception as exc:
            message = f"Error: {exc}"
            if console:
                console.print(message, style="red")
            else:
                print(message)
            continue

        answer = result.get("answer") or "I don't have enough information to answer that based on available sources."
        route = result.get("route", "unknown")
        sources = result.get("sources", [])

        if console:
            console.print(Panel(answer, title=f"Assistant - route: {route}"))
            if sources:
                console.print("Sources:")
                for source in sources[:8]:
                    console.print(f"- {source}")
        else:
            print(f"\nAssistant [{route}]: {answer}")
            if sources:
                print("Sources:")
                for source in sources[:8]:
                    print(f"- {source}")


if __name__ == "__main__":
    run_cli()

