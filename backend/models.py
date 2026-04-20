from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Literal, Optional


ENTRY_TYPES = Literal["bug_fix", "insight", "solution"]
MEMORY_STATUS = Literal["active", "deprecated", "superseded"]


class MemoryEntry(BaseModel):
    agent_id: str
    entry_type: ENTRY_TYPES
    content: str
    tags: list[str] = []
    version: int = 1
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # Memory lifecycle fields
    status: MEMORY_STATUS = "active"
    upvotes: int = 0
    downvotes: int = 0
    superseded_by: Optional[str] = None   # ID of the newer memory that replaces this


class MemoryEntryResponse(BaseModel):
    id: str
    message: str


class SearchResult(BaseModel):
    id: str
    content: str
    agent_id: str
    entry_type: str
    tags: list[str]
    version: int
    timestamp: str
    score: float
    # Lifecycle fields
    status: str = "active"
    upvotes: int = 0
    downvotes: int = 0
    superseded_by: Optional[str] = None


class VoteRequest(BaseModel):
    direction: Literal["up", "down"]


class DeprecateRequest(BaseModel):
    reason: str = ""
    superseded_by: Optional[str] = None   # ID of the replacement memory


class UpdateMemoryRequest(BaseModel):
    """Write a new version of an existing memory, auto-deprecates the old one."""
    agent_id: str
    entry_type: ENTRY_TYPES
    content: str
    tags: list[str] = []