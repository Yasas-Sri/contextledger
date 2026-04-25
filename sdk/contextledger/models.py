"""SDK-side models (mirrors backend, no FastAPI dependency)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class MemoryEntry:
    agent_id: str
    entry_type: str          # "bug_fix" | "insight" | "solution"
    content: str
    tags: list[str] = field(default_factory=list)
    version: int = 1
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class SearchResult:
    id: str
    content: str
    agent_id: str
    entry_type: str
    tags: list[str]
    version: int
    timestamp: str
    score: float
    status: str = "active"
    upvotes: int = 0
    downvotes: int = 0
    superseded_by: Optional[str] = None

    def is_stale(self) -> bool:
        """Heuristic: more downvotes than upvotes, or explicitly deprecated."""
        return self.status != "active" or self.downvotes > self.upvotes

    def __repr__(self):
        score_str = f"{self.score:.2f}" if self.score < 1.0 else ""
        score_part = f" score={score_str}" if score_str else ""
        status_part = f" [{self.status}]" if self.status != "active" else ""
        return (
            f"<Memory {self.id[:8]} "
            f"agent={self.agent_id} type={self.entry_type}"
            f"{score_part}{status_part} "
            f"v{self.version} +{self.upvotes}/-{self.downvotes}>"
        )