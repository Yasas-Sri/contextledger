"""
integrations/langchain_tool.py
Drop-in LangChain Tool for ContextLedger Lite.

Usage:
    from integrations.langchain_tool import build_contextledger_tools
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI   # or any LLM

    tools = build_contextledger_tools(
        base_url="http://localhost:8000",
        api_key="dev-secret-key",
    )

    llm = ChatOpenAI(model="gpt-4o-mini")
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
    agent.run("How do we handle database connection pool exhaustion?")
    # The agent will automatically search ContextLedger before answering.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from contextledger import ContextLedgerClient

try:
    from langchain.tools import Tool, StructuredTool
    from langchain.pydantic_v1 import BaseModel, Field as LCField
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False



class RecallInput(BaseModel):
    query: str = LCField(description="Natural language question to search agent memory for")
    entry_type: str = LCField(
        default="",
        description="Optional filter: 'bug_fix', 'insight', or 'solution'"
    )


class RememberInput(BaseModel):
    agent_id: str = LCField(description="ID of the agent storing this memory")
    entry_type: str = LCField(description="One of: bug_fix, insight, solution")
    content: str = LCField(description="The knowledge to store")
    tags: str = LCField(default="", description="Comma-separated tags, e.g. 'python,threading'")


class VoteInput(BaseModel):
    entry_id: str = LCField(description="The memory entry ID to vote on")
    direction: str = LCField(description="'up' to upvote, 'down' to downvote")



def build_contextledger_tools(
    base_url: str = "http://localhost:8000",
    api_key: str = "dev-secret-key",
    agent_id: str = "langchain-agent",
) -> list:
    """
    Returns a list of LangChain Tools for interacting with ContextLedger.

    Tools provided:
      - recall_from_memory   Search shared agent knowledge base
      - store_in_memory      Write a new memory entry
      - vote_on_memory       Upvote/downvote a memory for quality signal
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("langchain is not installed. Run: pip install langchain langchain-openai")

    ledger = ContextLedgerClient(base_url=base_url, api_key=api_key)

    def recall_fn(query: str, entry_type: str = "") -> str:
        results = ledger.recall(
            query=query,
            entry_type=entry_type if entry_type else None,
            limit=3,
        )
        if not results:
            return "No relevant memories found in the shared knowledge base."

        lines = [f"Found {len(results)} relevant memories from the shared agent knowledge base:\n"]
        for i, r in enumerate(results, 1):
            stale_warn = " ⚠️ [MAY BE STALE — downvotes > upvotes]" if r.is_stale() else ""
            lines.append(
                f"{i}. [{r.agent_id}] [{r.entry_type}] (score: {r.score:.2f}){stale_warn}\n"
                f"   {r.content}\n"
                f"   Tags: {', '.join(r.tags)} | v{r.version} | 👍{r.upvotes} 👎{r.downvotes}"
            )
        return "\n".join(lines)

    def remember_fn(agent_id: str, entry_type: str, content: str, tags: str = "") -> str:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        entry_id = ledger.remember(
            agent_id=agent_id,
            entry_type=entry_type,
            content=content,
            tags=tag_list,
        )
        return f"Memory stored successfully with ID: {entry_id}"

    def vote_fn(entry_id: str, direction: str) -> str:
        if direction == "up":
            r = ledger.upvote(entry_id)
            return f"Upvoted memory {entry_id[:8]}. Total: 👍{r.upvotes} 👎{r.downvotes}"
        else:
            r = ledger.downvote(entry_id)
            return f"Downvoted memory {entry_id[:8]}. Total: 👍{r.upvotes} 👎{r.downvotes}"

    return [
        StructuredTool.from_function(
            func=recall_fn,
            name="recall_from_memory",
            description=(
                "Search the shared AI agent knowledge base for relevant bug fixes, "
                "insights, and solutions. Use this BEFORE attempting to answer any "
                "coding or technical question — a previous agent may have already "
                "solved it. Input: a natural language query."
            ),
            args_schema=RecallInput,
        ),
        StructuredTool.from_function(
            func=remember_fn,
            name="store_in_memory",
            description=(
                "Store a new piece of knowledge in the shared agent memory. "
                "Use this after discovering a bug fix, insight, or solution "
                "that other agents could benefit from."
            ),
            args_schema=RememberInput,
        ),
        StructuredTool.from_function(
            func=vote_fn,
            name="vote_on_memory",
            description=(
                "Upvote a memory if it was accurate and helpful. "
                "Downvote it if the information was stale, wrong, or unhelpful. "
                "This keeps the shared knowledge base healthy over time."
            ),
            args_schema=VoteInput,
        ),
    ]



if __name__ == "__main__":
    print("ContextLedger LangChain Tool Demo")
    print("=" * 50)
    print("(Runs without LLM — shows raw tool output)\n")

    ledger = ContextLedgerClient(base_url="http://localhost:8000", api_key="dev-secret-key")

    # Simulate what a LangChain agent would do before answering a coding question
    query = "how to fix database connection pool exhaustion"
    print(f'Agent question: "{query}"\n')
    print("Step 1: Agent calls recall_from_memory tool...\n")

    results = ledger.recall(query, limit=3)
    if results:
        print(f"  Found {len(results)} memories:\n")
        for r in results:
            print(f"  [{r.agent_id}] score={r.score:.3f}")
            print(f"  {r.content[:100]}...")
            print(f"  Tags: {', '.join(r.tags)} | 👍{r.upvotes} 👎{r.downvotes}\n")

        # Agent upvotes the most relevant result
        best = results[0]
        print(f"Step 2: Agent upvotes most useful memory ({best.id[:8]})...")
        updated = ledger.upvote(best.id)
        print(f"  👍 {updated.upvotes} 👎 {updated.downvotes}\n")
    else:
        print("  No memories found. Agent stores its own solution...\n")
        entry_id = ledger.remember(
            agent_id="langchain-agent",
            entry_type="bug_fix",
            content="Wrap all DB calls in try/finally to guarantee connection release.",
            tags=["database", "connection-pool"],
        )
        print(f"  Stored new memory: {entry_id}")