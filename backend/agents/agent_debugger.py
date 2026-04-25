"""
agent_debugger.py
Simulates an AI agent that discovers and stores bug fixes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import MemoryEntry
from memory import MEMORY_STORE

MEMORIES = [
    MemoryEntry(
        agent_id="agent-debugger",
        entry_type="bug_fix",
        content="Fixed race condition in the thread pool by wrapping shared state with a threading.Lock. The bug caused intermittent crashes under high concurrency.",
        tags=["threading", "concurrency", "python", "crash"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-debugger",
        entry_type="bug_fix",
        content="Resolved null pointer exception in the authentication module. Root cause was missing validation before accessing user.profile when the OAuth token was expired.",
        tags=["auth", "null-pointer", "oauth", "python"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-debugger",
        entry_type="bug_fix",
        content="Patched memory leak in the WebSocket connection handler. Connections were not being closed on client disconnect, causing the server to run out of file descriptors after ~500 connections.",
        tags=["websocket", "memory-leak", "file-descriptors", "server"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-debugger",
        entry_type="bug_fix",
        content="Fixed off-by-one error in pagination logic. Page 1 was returning items 0-9 correctly but page 2 was starting at item 11, skipping item 10. Changed (page * size) to ((page-1) * size).",
        tags=["pagination", "off-by-one", "api"],
        version=1,
    ),
    MemoryEntry(
        agent_id="agent-debugger",
        entry_type="bug_fix",
        content="Resolved database connection pool exhaustion under load. Connections were acquired but never released when exceptions occurred mid-transaction. Wrapped all DB calls in try/finally to guarantee release.",
        tags=["database", "connection-pool", "exception-handling", "performance"],
        version=2,
    ),
]


def run():
    print(f"[agent-debugger] Writing {len(MEMORIES)} bug fix memories...")
    for m in MEMORIES:
        entry_id = MEMORY_STORE.write(m)
        print(f"  ✓ Stored: {m.content[:60]}... [{entry_id[:8]}]")
    print(f"[agent-debugger] Done.\n")


if __name__ == "__main__":
    run()