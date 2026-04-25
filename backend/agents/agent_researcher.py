"""
agent_researcher.py
Simulates an AI agent that discovers and stores technical insights.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import MemoryEntry
from memory import MEMORY_STORE

MEMORIES = [
    MemoryEntry(
        agent_id="agent-researcher",
        entry_type="insight",
        content="Transformer attention with rotary positional embeddings (RoPE) generalizes better to longer sequences than absolute positional encoding. Switch to RoPE if your model needs to handle variable-length inputs beyond training context.",
        tags=["transformers", "attention", "rope", "embeddings", "llm"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-researcher",
        entry_type="insight",
        content="Batch normalization hurts performance in small-batch or online learning scenarios. Layer normalization is more stable across batch sizes and is preferred in modern transformer architectures.",
        tags=["normalization", "batch-norm", "layer-norm", "training"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-researcher",
        entry_type="insight",
        content="Vector similarity search recall drops sharply above 90% dataset saturation with HNSW. Rebuild the index or increase ef_construction when insert volume exceeds ~85% of initial capacity.",
        tags=["hnsw", "vector-search", "recall", "index", "performance"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-researcher",
        entry_type="insight",
        content="Using cosine similarity instead of L2 distance for text embeddings consistently yields better semantic relevance. Normalize all embeddings before insertion for consistent cosine behavior.",
        tags=["cosine-similarity", "embeddings", "semantic-search", "vector-db"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-researcher",
        entry_type="insight",
        content="RAG retrieval quality improves significantly when query is rewritten before embedding. Prompt the LLM to reformulate the user question as a factual declarative sentence before embedding and searching.",
        tags=["rag", "retrieval", "query-rewriting", "llm", "embeddings"],
        version=1,
    ),
]


def run():
    print(f"[agent-researcher] Writing {len(MEMORIES)} insight memories...")
    for m in MEMORIES:
        entry_id = MEMORY_STORE.write(m)
        print(f"  ✓ Stored: {m.content[:60]}... [{entry_id[:8]}]")
    print(f"[agent-researcher] Done.\n")


if __name__ == "__main__":
    run()