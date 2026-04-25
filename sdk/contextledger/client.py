"""
ContextLedger Python Client SDK

Usage:
    from contextledger import ContextLedgerClient

    ledger = ContextLedgerClient(
        base_url="http://localhost:8000",
        api_key="dev-secret-key",
    )

    # Store a memory
    entry_id = ledger.remember(
        agent_id="my-agent",
        entry_type="bug_fix",
        content="Fixed the race condition by adding a mutex lock.",
        tags=["threading", "python"],
    )

    # Search shared memory
    results = ledger.recall("how to fix threading issues")
    for r in results:
        print(r)

    # Vote on a memory
    ledger.upvote(entry_id)
    ledger.downvote(entry_id)

    # Deprecate stale knowledge
    ledger.deprecate(entry_id, reason="No longer relevant in Python 3.12+")

    # Release a new version
    new_id = ledger.update(entry_id, content="Updated fix using asyncio.Lock instead.")
"""

import httpx
from typing import Optional
from .models import MemoryEntry, SearchResult


class ContextLedgerError(Exception):
    pass


class AuthError(ContextLedgerError):
    pass


class NotFoundError(ContextLedgerError):
    pass


class ContextLedgerClient:
    """
    Python client for the ContextLedger Lite API.

    All write operations (remember, vote, deprecate, update) require an api_key.
    Read operations (recall, timeline, get) are public.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "",
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ── Private helpers ───────────────────────────────────────────────────────

    @property
    def _auth_headers(self) -> dict:
        return {"X-API-Key": self.api_key}

    def _raise_for_status(self, resp: httpx.Response):
        if resp.status_code == 401:
            raise AuthError("Invalid or missing API key.")
        if resp.status_code == 404:
            raise NotFoundError(resp.json().get("detail", "Not found."))
        if resp.status_code >= 400:
            raise ContextLedgerError(f"API error {resp.status_code}: {resp.text}")

    def _to_result(self, data: dict) -> SearchResult:
        return SearchResult(
            id=data.get("id", ""),
            content=data["content"],
            agent_id=data["agent_id"],
            entry_type=data["entry_type"],
            tags=data.get("tags", []),
            version=data.get("version", 1),
            timestamp=data.get("timestamp", ""),
            score=data.get("score", 1.0),
            status=data.get("status", "active"),
            upvotes=data.get("upvotes", 0),
            downvotes=data.get("downvotes", 0),
            superseded_by=data.get("superseded_by"),
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    def remember(
        self,
        agent_id: str,
        entry_type: str,
        content: str,
        tags: list[str] = None,
        version: int = 1,
    ) -> str:
        """
        Store a memory entry. Returns the entry ID.

        Example:
            entry_id = ledger.remember(
                agent_id="agent-debugger",
                entry_type="bug_fix",
                content="Fixed null pointer by validating token before access.",
                tags=["auth", "python"],
            )
        """
        resp = self._client.post(
            "/memory",
            headers=self._auth_headers,
            json={
                "agent_id": agent_id,
                "entry_type": entry_type,
                "content": content,
                "tags": tags or [],
                "version": version,
            },
        )
        self._raise_for_status(resp)
        return resp.json()["id"]

    # ── Read ──────────────────────────────────────────────────────────────────

    def recall(
        self,
        query: str,
        agent_id: str = None,
        entry_type: str = None,
        tag: str = None,
        include_deprecated: bool = False,
        limit: int = 5,
    ) -> list[SearchResult]:
        """
        Semantic search across shared memory.

        Example:
            results = ledger.recall(
                "how to handle database connection errors",
                entry_type="bug_fix",
                limit=3,
            )
        """
        params = {"q": query, "limit": limit, "include_deprecated": include_deprecated}
        if agent_id:
            params["agent_id"] = agent_id
        if entry_type:
            params["entry_type"] = entry_type
        if tag:
            params["tag"] = tag

        resp = self._client.get("/search", params=params)
        self._raise_for_status(resp)
        return [self._to_result(r) for r in resp.json()]

    def get(self, entry_id: str) -> SearchResult:
        """Fetch a single memory by ID."""
        resp = self._client.get(f"/memory/{entry_id}")
        self._raise_for_status(resp)
        return self._to_result(resp.json())

    def timeline(self, limit: int = 50, include_deprecated: bool = True) -> list[SearchResult]:
        """Get all memories sorted newest first."""
        resp = self._client.get(
            "/timeline",
            params={"limit": limit, "include_deprecated": include_deprecated},
        )
        self._raise_for_status(resp)
        return [self._to_result(r) for r in resp.json()]

    def stats(self) -> dict:
        """Get memory statistics."""
        resp = self._client.get("/stats")
        self._raise_for_status(resp)
        return resp.json()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def upvote(self, entry_id: str) -> SearchResult:
        """
        Upvote a memory — signals this knowledge is accurate and useful.

        Example:
            ledger.upvote(entry_id)
        """
        resp = self._client.post(
            f"/memory/{entry_id}/vote",
            headers=self._auth_headers,
            json={"direction": "up"},
        )
        self._raise_for_status(resp)
        return self._to_result(resp.json())

    def downvote(self, entry_id: str) -> SearchResult:
        """
        Downvote a memory — signals this knowledge may be stale or incorrect.
        High downvote count is a signal to agents to treat results with caution.

        Example:
            ledger.downvote(old_entry_id)
        """
        resp = self._client.post(
            f"/memory/{entry_id}/vote",
            headers=self._auth_headers,
            json={"direction": "down"},
        )
        self._raise_for_status(resp)
        return self._to_result(resp.json())

    def deprecate(
        self,
        entry_id: str,
        reason: str = "",
        superseded_by: str = None,
    ) -> bool:
        """
        Mark a memory as deprecated (excluded from future searches by default).
        Optionally link to the ID of the memory that replaces it.

        Example:
            ledger.deprecate(
                old_id,
                reason="No longer valid in Python 3.12+",
                superseded_by=new_id,
            )
        """
        resp = self._client.post(
            f"/memory/{entry_id}/deprecate",
            headers=self._auth_headers,
            json={"reason": reason, "superseded_by": superseded_by},
        )
        self._raise_for_status(resp)
        return True

    def update(
        self,
        entry_id: str,
        content: str,
        agent_id: str = None,
        entry_type: str = None,
        tags: list[str] = None,
    ) -> str:
        """
        Write a new version of a memory. Auto-increments version number
        and marks the old entry as 'superseded'. Returns the new entry ID.

        Example:
            new_id = ledger.update(
                old_id,
                content="Updated: use asyncio.Lock instead of threading.Lock for async code.",
                tags=["asyncio", "python", "concurrency"],
            )
        """
        old = self.get(entry_id)
        resp = self._client.post(
            f"/memory/{entry_id}/update",
            headers=self._auth_headers,
            json={
                "agent_id":   agent_id or old.agent_id,
                "entry_type": entry_type or old.entry_type,
                "content":    content,
                "tags":       tags if tags is not None else old.tags,
            },
        )
        self._raise_for_status(resp)
        return resp.json()["id"]

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()