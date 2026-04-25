import sys
import os
import time

# Add the local SDK to the python path so we don't have to pip install it first
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "sdk"))

from contextledger.client import ContextLedgerClient, AuthError

API_BASE = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "dev-secret-key")

def run_sdk_simulation():
    print("\n╔══════════════════════════════════════╗")
    print("║   ContextLedger SDK Simulation       ║")
    print("╚══════════════════════════════════════╝\n")
    
    print(f"Connecting to {API_BASE} using Python SDK...\n")
    
    # Initialize the client from the SDK
    ledger = ContextLedgerClient(base_url=API_BASE, api_key=API_KEY)
    
    try:
        # 1. Store Memories using the SDK
        print("Phase 1: Agents writing memories via SDK...")
        
        id1 = ledger.remember(
            agent_id="sdk-agent-alpha",
            entry_type="insight",
            content="If a user requests React code, sometimes vanilla JS is faster for hackathons, but we can do React too.",
            tags=["hackathon", "react", "ui"]
        )
        print(f"  ✓ Stored insight memory (ID: {id1})")
        
        id2 = ledger.remember(
            agent_id="sdk-agent-beta",
            entry_type="bug_fix",
            content="Fixed Connection Refused error by ensuring VectorAI connects to localhost instead of Docker hostname.",
            tags=["docker", "networking", "vectorai"]
        )
        print(f"  ✓ Stored bug_fix memory (ID: {id2})")

        # 2. Voting using the SDK
        print("\nPhase 2: Voting on memories...")
        ledger.upvote(id2)
        ledger.upvote(id2)
        print(f"  ✓ Upvoted memory {id2} twice")
        ledger.downvote(id1)
        print(f"  ✓ Downvoted memory {id1} once")

        # Give Vector DB a tiny fraction of a second to index
        time.sleep(1)

        # 3. Search using the SDK
        print("\nPhase 3: Semantic Search via SDK...")
        results = ledger.recall("how to fix network connection issues?", limit=2)
        for r in results:
            print(f"  🔍 Score: {r.score:.3f} | Agent: {r.agent_id} | Content: {r.content[:60]}...")
            
        # 4. Fetch Timeline using the SDK
        print("\nPhase 4: Fetching Timeline...")
        timeline = ledger.timeline(limit=3)
        for r in timeline:
            print(f"  ⏱️ [{r.timestamp}] {r.agent_id}: {r.content[:50]}... (+{r.upvotes}/-{r.downvotes})")
            
        # 5. Deprecate obsolete memories
        print("\nPhase 5: Deprecating stale memories...")
        ledger.deprecate(id1, reason="Moving on from this topic.")
        print(f"  ✓ Deprecated memory {id1}")

    except AuthError:
        print("  ✗ Authentication failed! Invalid API key.")
    except Exception as e:
        print(f"  ✗ An error occurred: {e}")
    finally:
        ledger.close()
        
    print("\n SDK simulation complete.\n")

if __name__ == "__main__":
    run_sdk_simulation()
