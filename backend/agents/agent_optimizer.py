"""
agent_optimizer.py
Simulates an AI agent that discovers and stores performance solutions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import MemoryEntry
from memory import MEMORY_STORE

MEMORIES = [
    MemoryEntry(
        agent_id="agent-optimizer",
        entry_type="solution",
        content="Reduced API latency by 40% by batching database writes. Instead of one INSERT per request, buffer writes in a queue and flush every 100ms or 50 items, whichever comes first.",
        tags=["database", "batching", "latency", "performance", "api"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-optimizer",
        entry_type="solution",
        content="Cut cold-start time by 60% by pre-loading the embedding model at server startup instead of lazily on first request. Add a /health endpoint that confirms model is ready before routing traffic.",
        tags=["cold-start", "embeddings", "startup", "performance"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-optimizer",
        entry_type="solution",
        content="Improved vector search throughput 3x by switching from sequential to parallel query execution using asyncio.gather. Each agent query can now run concurrently instead of blocking the event loop.",
        tags=["async", "concurrency", "vector-search", "throughput", "asyncio"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-optimizer",
        entry_type="solution",
        content="Reduced memory usage by 45% by streaming large dataset embeddings in chunks of 256 rather than loading all documents into memory at once before embedding.",
        tags=["memory", "streaming", "embeddings", "chunking", "optimization"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-optimizer",
        entry_type="solution",
        content="Eliminated redundant re-embedding of identical content by adding a content hash cache. Before embedding, check if SHA256(content) exists in the cache and reuse the stored vector.",
        tags=["caching", "embeddings", "deduplication", "performance", "hash"],
        version=2,
    ),
]


def run():
    print(f"[agent-optimizer] Writing {len(MEMORIES)} solution memories...")
    for m in MEMORIES:
        entry_id = MEMORY_STORE.write(m)
        print(f"  ✓ Stored: {m.content[:60]}... [{entry_id[:8]}]")
    print(f"[agent-optimizer] Done.\n")


if __name__ == "__main__":
    run()