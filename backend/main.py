"""
main.py - ContextLedger Lite API
"""

from fastapi import FastAPI, Query, Security, HTTPException, status, Path
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

from models import (
    MemoryEntry, MemoryEntryResponse, SearchResult,
    VoteRequest, DeprecateRequest, UpdateMemoryRequest
)
from memory import MEMORY_STORE

load_dotenv()

_API_KEY = os.getenv("API_KEY", "dev-secret-key")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(_api_key_header)):
    if key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Pass X-API-Key header.",
        )
    return key


def get_or_404(entry_id: str):
    entry = MEMORY_STORE.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{entry_id}' not found.")
    return entry


app = FastAPI(
    title="ContextLedger Lite",
    description="Shared searchable memory for AI agent teams",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Write (PROTECTED) ─────────────────────────────────────────────────────────

@app.post("/memory", response_model=MemoryEntryResponse, tags=["Memory"])
def write_memory(entry: MemoryEntry, _key: str = Security(require_api_key)):
    """Store a new memory entry. Requires X-API-Key header."""
    entry_id = MEMORY_STORE.write(entry)
    return MemoryEntryResponse(id=entry_id, message="Memory stored successfully.")


# ── Read single entry (PUBLIC) ────────────────────────────────────────────────

@app.get("/memory/{entry_id}", response_model=SearchResult, tags=["Memory"])
def get_memory(entry_id: str = Path(...)):
    """Fetch a single memory entry by ID."""
    return get_or_404(entry_id)


# ── Search (PUBLIC) ───────────────────────────────────────────────────────────

@app.get("/search", response_model=list[SearchResult], tags=["Memory"])
def search_memory(
    q: str = Query(...),
    agent_id: str | None = Query(None),
    entry_type: str | None = Query(None),
    tag: str | None = Query(None),
    include_deprecated: bool = Query(False, description="Include deprecated/superseded memories"),
    limit: int = Query(5, ge=1, le=20),
):
    """Semantic search with filters. Active memories only by default."""
    return MEMORY_STORE.search(
        query=q,
        agent_id=agent_id,
        entry_type=entry_type,
        tag=tag,
        include_deprecated=include_deprecated,
        limit=limit,
    )


# ── Timeline (PUBLIC) ─────────────────────────────────────────────────────────

@app.get("/timeline", response_model=list[SearchResult], tags=["Memory"])
def get_timeline(
    limit: int = Query(50, ge=1, le=200),
    include_deprecated: bool = Query(True),
):
    return MEMORY_STORE.get_all(limit=limit, include_deprecated=include_deprecated)


# ── Vote (PROTECTED) ──────────────────────────────────────────────────────────

@app.post("/memory/{entry_id}/vote", response_model=SearchResult, tags=["Lifecycle"])
def vote_memory(
    vote: VoteRequest,
    entry_id: str = Path(...),
    _key: str = Security(require_api_key),
):
    """
    Upvote or downvote a memory entry.
    High downvotes signal agents that this knowledge may be stale.
    """
    get_or_404(entry_id)
    updated = MEMORY_STORE.vote(entry_id, vote.direction)
    return updated


# ── Deprecate (PROTECTED) ─────────────────────────────────────────────────────

@app.post("/memory/{entry_id}/deprecate", response_model=MemoryEntryResponse, tags=["Lifecycle"])
def deprecate_memory(
    req: DeprecateRequest,
    entry_id: str = Path(...),
    _key: str = Security(require_api_key),
):
    """
    Mark a memory as deprecated (no longer valid).
    Optionally point to a superseding memory ID.
    Deprecated memories are excluded from search by default.
    """
    get_or_404(entry_id)
    MEMORY_STORE.deprecate(entry_id, req.reason, req.superseded_by or "")
    return MemoryEntryResponse(id=entry_id, message="Memory deprecated.")


# ── Update / new version (PROTECTED) ─────────────────────────────────────────

@app.post("/memory/{entry_id}/update", response_model=MemoryEntryResponse, tags=["Lifecycle"])
def update_memory(
    req: UpdateMemoryRequest,
    entry_id: str = Path(...),
    _key: str = Security(require_api_key),
):
    """
    Write a new version of an existing memory.
    Auto-increments version number and marks the old entry as 'superseded'.
    The old entry remains in the timeline for audit purposes.
    """
    get_or_404(entry_id)
    new_entry = MemoryEntry(
        agent_id=req.agent_id,
        entry_type=req.entry_type,
        content=req.content,
        tags=req.tags,
    )
    new_id = MEMORY_STORE.update_version(entry_id, new_entry)
    return MemoryEntryResponse(id=new_id, message=f"New version stored. Old entry superseded.")


# ── Stats (PUBLIC) ────────────────────────────────────────────────────────────

@app.get("/stats", tags=["Meta"])
def get_stats():
    all_entries = MEMORY_STORE.get_all(limit=1000, include_deprecated=True)
    return {
        "total_memories": MEMORY_STORE.count(),
        "active": sum(1 for e in all_entries if e.status == "active"),
        "deprecated": sum(1 for e in all_entries if e.status == "deprecated"),
        "superseded": sum(1 for e in all_entries if e.status == "superseded"),
    }


# ── Serve frontend (PUBLIC) ───────────────────────────────────────────────────

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/", include_in_schema=False)
def serve_ui():
    return FileResponse(os.path.join(frontend_path, "index.html"))