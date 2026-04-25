"""
memory.py - All vector DB calls live here.

Using Actian VectorAI DB (actiancortex) as the primary store.

Setup:
  1. Clone https://github.com/hackmamba-io/actian-vectorAI-db-beta
  2. pip install actiancortex-0.1.0b1-py3-none-any.whl
  3. docker compose up        (starts DB on localhost:50051)
"""

import os
import uuid
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv

from embedder import get_embedding
from models import MemoryEntry, SearchResult

load_dotenv()

VECTORAI_HOST = os.getenv("VECTORAI_HOST", "localhost:50051")
COLLECTION_NAME = "agent_memory"
VECTOR_DIM = 384   # all-MiniLM-L6-v2 output dimension


# ── Helpers ───────────────────────────────────────────────────────────────────

def _str_to_int_id(s: str) -> int:
    """VectorAI DB uses integer IDs. Derive a stable int from a UUID string."""
    return int(hashlib.md5(s.encode()).hexdigest()[:15], 16)

def _int_id_to_str(i: int) -> str:
    return str(i)

def _meta_to_result(entry_id: str, content: str, meta: dict, score: float = 1.0) -> SearchResult:
    return SearchResult(
        id=entry_id,
        content=content,
        agent_id=meta.get("agent_id", ""),
        entry_type=meta.get("entry_type", ""),
        tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
        version=int(meta.get("version", 1)),
        timestamp=meta.get("timestamp", ""),
        score=round(score, 4),
        status=meta.get("status", "active"),
        upvotes=int(meta.get("upvotes", 0)),
        downvotes=int(meta.get("downvotes", 0)),
        superseded_by=meta.get("superseded_by") or None,
    )


# ── Actian VectorAI DB Store ──────────────────────────────────────────────────

class ActianVectorAIMemoryStore:
    """
    Production store using Actian VectorAI DB (actiancortex).
    Requires Docker: docker compose up
    Uses gRPC on port 50051.
    """

    def __init__(self, host: str = None, port: int = 50051):
        if host:
            self.host = host
        else:
            self.host = os.environ.get("VECTORAI_HOST", "localhost:50051")
            
        print(f"[memory] Using Actian VectorAI DB (gRPC → {self.host})")
        
        try:
            from actian_vectorai import VectorAIClient, VectorParams, Distance, PointStruct, Field, FilterBuilder
        except ImportError:
            print("[error] Could not import actian_vectorai SDK")
            raise
        
        self.client = VectorAIClient(self.host)
        
        # Retry connection 
        import time
        max_retries = 10
        for _ in range(max_retries):
            try:
                self.client.connect()
                # Test connection by fetching collections
                _ = self.client.collections.list()
                print("[vectorai] Connected successfully to DB")
                break
            except Exception as e:
                print(f"[vectorai] Waiting for DB to be ready... {e}")
                time.sleep(2)
        else:
            raise RuntimeError("Could not connect to VectorAI DB after retries")

        self.collection_name = "agent_memories"
        
        self.PointStruct = PointStruct
        self.Field = Field
        self.FilterBuilder = FilterBuilder


        # if self.client.collections.exists(self.collection_name):
        #     self.client.collections.delete(self.collection_name)
        #     print(f"[vectorai] Dropped existing collection '{self.collection_name}' for clean demo")




          

        
        if not self.client.collections.exists(self.collection_name):
            self.client.collections.create(
                self.collection_name,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.Cosine)
            )
            print(f"[vectorai] Created collection '{self.collection_name}' (dim={VECTOR_DIM})")
        else:
            print(f"[vectorai] Connected to existing collection '{self.collection_name}'")

        # In-memory index: int_id -> (str_uuid, content, metadata)
        # Needed because get_many doesn't return IDs (known issue CRTX-233)
        self._index: dict[int, tuple[str, str, dict]] = {}
        # self._rebuild_index()

    def _payload(self, str_id: str, entry: MemoryEntry, content: str) -> dict:
        return {
            "str_id":       str_id,
            "content":      content,
            "agent_id":     entry.agent_id,
            "entry_type":   entry.entry_type,
            "tags":         ",".join(entry.tags),
            "version":      entry.version,
            "timestamp":    entry.timestamp,
            "status":       entry.status,
            "upvotes":      entry.upvotes,
            "downvotes":    entry.downvotes,
            "superseded_by": entry.superseded_by or "",
        }

    def write(self, entry: MemoryEntry) -> str:
        str_id = str(uuid.uuid4())
        int_id = _str_to_int_id(str_id)
        embedding = get_embedding(entry.content)
        payload = self._payload(str_id, entry, entry.content)

        self.client.points.upsert(
            self.collection_name,
            [self.PointStruct(id=int_id, vector=embedding, payload=payload)]
        )
        self._index[int_id] = (str_id, entry.content, payload)
        return str_id

    def get_by_id(self, str_id: str) -> SearchResult | None:
        int_id = _str_to_int_id(str_id)
        if int_id not in self._index:
            return None
        _, content, meta = self._index[int_id]
        return _meta_to_result(str_id, content, meta)

    def update_metadata(self, str_id: str, updates: dict) -> bool:
        int_id = _str_to_int_id(str_id)
        if int_id not in self._index:
            return False
        str_id_stored, content, meta = self._index[int_id]
        meta.update(updates)
        # Re-upsert with updated payload (VectorAI DB upsert = insert or update)
        # We need the original vector — get it from the DB
        points = self.client.points.get(self.collection_name, ids=[int_id])
        if points and len(points) > 0 and points[0].vector:
            self.client.points.upsert(
                self.collection_name,
                [self.PointStruct(id=int_id, vector=list(points[0].vector), payload=meta)]
            )
        self._index[int_id] = (str_id_stored, content, meta)
        return True

    def vote(self, str_id: str, direction: str) -> SearchResult | None:
        existing = self.get_by_id(str_id)
        if not existing:
            return None
        updates = {}
        if direction == "up":
            updates["upvotes"] = existing.upvotes + 1
        else:
            updates["downvotes"] = existing.downvotes + 1
        self.update_metadata(str_id, updates)
        return self.get_by_id(str_id)

    def deprecate(self, str_id: str, reason: str = "", superseded_by: str = "") -> bool:
        return self.update_metadata(str_id, {
            "status": "deprecated",
            "superseded_by": superseded_by or "",
        })

    def update_version(self, old_str_id: str, new_entry: MemoryEntry) -> str:
        old = self.get_by_id(old_str_id)
        if old:
            new_entry.version = old.version + 1
        new_id = self.write(new_entry)
        if old:
            self.update_metadata(old_str_id, {
                "status": "superseded",
                "superseded_by": new_id,
            })
        return new_id

    def search(
        self,
        query: str,
        agent_id: str | None = None,
        entry_type: str | None = None,
        tag: str | None = None,
        include_deprecated: bool = False,
        limit: int = 5,
    ) -> list[SearchResult]:
        embedding = get_embedding(query)

        # Build VectorAI DB Filter DSL
        builder = self.FilterBuilder()
        if not include_deprecated:
            builder = builder.must(self.Field("status").eq("active"))
        if agent_id:
            builder = builder.must(self.Field("agent_id").eq(agent_id))
        if entry_type:
            builder = builder.must(self.Field("entry_type").eq(entry_type))

        use_filter = agent_id or entry_type or (not include_deprecated)

        if use_filter:
            f = builder.build()
            raw = self.client.points.search(
                self.collection_name, vector=embedding, filter=f, limit=limit
            )
        else:
            raw = self.client.points.search(self.collection_name, vector=embedding, limit=limit)

        results = []
        for point in raw:
            payload = point.payload or {}
            str_id = payload.get("str_id", str(point.id))
            content = payload.get("content", "")
            r = _meta_to_result(str_id, content, payload, score=point.score)
            # Tag filter (post-filter since VectorAI DB filter DSL uses exact match)
            if tag and tag not in r.tags:
                continue
            results.append(r)
        return results

    def get_all(self, limit: int = 100, include_deprecated: bool = True) -> list[SearchResult]:
        output = []
        try:
            # Query the database directly for timeline items using a dummy vector
            raw = self.client.points.search(
                self.collection_name, 
                vector=[0.0] * VECTOR_DIM, 
                limit=limit
            )
            
            for point in raw:
                payload = point.payload or {}
                str_id = payload.get("str_id", str(point.id))
                content = payload.get("content", "")
                r = _meta_to_result(str_id, content, payload, score=point.score)
                if include_deprecated or r.status == "active":
                    output.append(r)
        except Exception as e:
            print(f"[vectorai] Could not fetch all points from DB: {e}")
            # Fallback to _index if DB search fails
            for int_id, (str_id, content, payload) in self._index.items():
                r = _meta_to_result(str_id, content, payload)
                if include_deprecated or r.status == "active":
                    output.append(r)
                    
        # Sort by timestamp, newest first
        output.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Take exactly the limit required
        return output[:limit]

    def count(self) -> int:
        try:
            return self.client.points.count(self.collection_name)
        except Exception:
            return len(self._index)


# ── Initialize store ────────────────────────────────────────────────────────

print("[memory] Using Actian VectorAI DB (gRPC → localhost:50051)")
MEMORY_STORE = ActianVectorAIMemoryStore()