"""
simulate_agents.py
Runs all three agents to populate the shared memory,
then demonstrates cross-agent retrieval with filtered search.

The agents call the API directly (with API key auth),
just like real agents would in production.

Run:
  # Option A: direct (no API server needed)
  python simulate_agents.py --direct

  # Option B: via API (start server first)
  uvicorn backend.main:app --reload
  python simulate_agents.py
"""

import sys
import os
import argparse

# -- Direct mode: bypass API, call memory layer directly ---------------------
def run_direct():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    from agents.agent_debugger import run as run_debugger
    from agents.agent_researcher import run as run_researcher
    from agents.agent_optimizer import run as run_optimizer
    from memory import MEMORY_STORE

    print("\n╔══════════════════════════════════════╗")
    print("║   ContextLedger Lite — Direct Mode   ║")
    print("╚══════════════════════════════════════╝\n")

    print("Phase 1: Agents writing to shared memory...\n")
    run_debugger()
    run_researcher()
    run_optimizer()

    print("Phase 2: Demonstrating cross-agent retrieval...\n")
    demo_search_direct(MEMORY_STORE)

    print("✅ Simulation complete.")
    print("   Start the API: cd backend && uvicorn main:app --reload")
    print("   Then open:     http://localhost:8000\n")


# -- API mode: agents talk to the running FastAPI server ----------------------
def run_via_api(base_url: str, api_key: str):
    import json
    try:
        import httpx
    except ImportError:
        print("[error] httpx not installed. Run: pip install httpx")
        sys.exit(1)

    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    MEMORIES = [
        # Debugger
        {"agent_id": "agent-debugger", "entry_type": "bug_fix",
         "content": "Fixed race condition in thread pool using threading.Lock.",
         "tags": ["threading", "concurrency", "python"]},
        {"agent_id": "agent-debugger", "entry_type": "bug_fix",
         "content": "Resolved null pointer in auth module — validate token before accessing user.profile.",
         "tags": ["auth", "null-pointer", "oauth"]},
        # Researcher
        {"agent_id": "agent-researcher", "entry_type": "insight",
         "content": "RoPE positional embeddings generalise better to longer sequences than absolute encoding.",
         "tags": ["transformers", "rope", "llm"]},
        {"agent_id": "agent-researcher", "entry_type": "insight",
         "content": "Cosine similarity consistently outperforms L2 for semantic text search. Normalise embeddings.",
         "tags": ["cosine-similarity", "embeddings", "vector-db"]},
        # Optimizer
        {"agent_id": "agent-optimizer", "entry_type": "solution",
         "content": "Reduced API latency 40% by batching DB writes — flush every 100ms or 50 items.",
         "tags": ["database", "batching", "latency", "performance"]},
        {"agent_id": "agent-optimizer", "entry_type": "solution",
         "content": "Cut cold-start 60% by pre-loading embedding model at startup, not on first request.",
         "tags": ["cold-start", "embeddings", "startup"]},
    ]

    print("\n╔══════════════════════════════════════╗")
    print("║    ContextLedger Lite — API Mode     ║")
    print("╚══════════════════════════════════════╝\n")
    print(f"Connecting to {base_url} with API key authentication...\n")

    with httpx.Client(base_url=base_url,timeout=60.0) as client:
        # Write memories
        print("Phase 1: Agents writing memories via authenticated API...\n")
        for m in MEMORIES:
            resp = client.post("/memory", headers=headers, json=m)
            if resp.status_code == 200:
                print(f"  ✓ [{m['agent_id']}] {m['content'][:60]}...")
            elif resp.status_code == 401:
                print(f"  ✗ 401 Unauthorized — check your API key")
                sys.exit(1)
            else:
                print(f"  ✗ Error {resp.status_code}: {resp.text}")

        # Test auth rejection
        print("\nPhase 2: Testing auth rejection with wrong key...\n")
        bad_resp = client.post("/memory", headers={"X-API-Key": "wrong-key"},
                               json=MEMORIES[0])
        if bad_resp.status_code == 401:
            print("  ✓ Correctly rejected bad API key (401 Unauthorized)")
        else:
            print(f"  ! Unexpected status: {bad_resp.status_code}")

        # Demo searches (no auth needed)
        print("\nPhase 3: Cross-agent search (no auth required)...\n")
        queries = [
            ("database performance", None, None),
            ("memory leak", None, "bug_fix"),
            ("embeddings", "agent-researcher", None),
        ]
        for q, agent, etype in queries:
            params = {"q": q, "limit": 2}
            if agent: params["agent_id"] = agent
            if etype: params["entry_type"] = etype
            resp = client.get("/search", params=params)
            results = resp.json()
            print(f"  🔍 '{q}' (filters: agent={agent}, type={etype})")
            for r in results:
                print(f"     [{r['agent_id']}] score={r['score']:.3f} — {r['content'][:70]}...")
            print()

    print(" API simulation complete.\n")


# -- Direct mode search demo --------------------------------------------------
DEMO_QUERIES = [
    ("how to improve database performance", {}, ),
    ("memory issues and leaks",             {"entry_type": "bug_fix"}),
    ("make things faster",                  {"agent_id": "agent-optimizer"}),
    ("working with vector embeddings",      {"tag": "embeddings"}),
    ("concurrent and parallel execution",   {}),
]

def demo_search_direct(store):
    print("\n" + "=" * 60)
    print("  DEMO: Cross-Agent Semantic Search + Filtered Retrieval")
    print("=" * 60)
    for q, filters in DEMO_QUERIES:
        print(f"\n🔍 Query: \"{q}\"")
        print(f"   Filters: {filters if filters else 'none'}")
        results = store.search(query=q, limit=3, **filters)
        for i, r in enumerate(results, 1):
            print(f"\n   {i}. [{r.agent_id}] [{r.entry_type}] score={r.score:.3f}")
            print(f"      {r.content[:100]}...")
    print("\n" + "=" * 60)
    print(f"  Total memories: {store.count()}")
    print("=" * 60 + "\n")


# -- Entry point --------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct", action="store_true",
                        help="Bypass API, write directly to memory store (no server needed)")
    parser.add_argument("--url", default="http://localhost:8000",
                        help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--key", default=os.getenv("API_KEY", "dev-secret-key"),
                        help="API key for authentication")
    args = parser.parse_args()

    if args.direct:
        run_direct()
    else:
        run_via_api(args.url, args.key)