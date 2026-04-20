"""
embedder.py — Local embedding using sentence-transformers.

Model loading priority:
  1. ./models/all-MiniLM-L6-v2  
  2. HuggingFace download        
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

_LOCAL_MODEL_PATH = Path(__file__).parent.parent / "models" / MODEL_NAME

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        if _LOCAL_MODEL_PATH.exists():
            print(f"[embedder] Loading model from local path: {_LOCAL_MODEL_PATH}")
            _model = SentenceTransformer(str(_LOCAL_MODEL_PATH))
        else:
            print(f"[embedder] Local model not found at {_LOCAL_MODEL_PATH}")
            print(f"[embedder] Downloading '{MODEL_NAME}' from HuggingFace (run download_model.py to cache locally)...")
            _model = SentenceTransformer(MODEL_NAME)
        print("[embedder] ✓ Model ready.")
    return _model


def get_embedding(text: str) -> list[float]:
    model = _get_model()
    return model.encode(text, normalize_embeddings=True).tolist()