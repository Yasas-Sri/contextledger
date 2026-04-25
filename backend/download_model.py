"""
download_model.py — Pre-download the embedding model for offline use.

Run this ONCE before building your Docker image:
    python download_model.py

This saves the model to ./models/all-MiniLM-L6-v2 so it's baked
into the Docker image and never needs internet at runtime.
"""

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_DIR = Path(__file__).parent / "models" / MODEL_NAME


def download():
    print(f"[download_model] Downloading '{MODEL_NAME}' from HuggingFace...")
    print(f"[download_model] Saving to: {MODEL_DIR}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer(MODEL_NAME)
    model.save(str(MODEL_DIR))

    print(f"[download_model] ✓ Model saved successfully.")

    # Quick smoke test
    print(f"[download_model] Running smoke test...")
    test_embedding = model.encode("test sentence", normalize_embeddings=True)
    assert len(test_embedding) == 384, "Unexpected embedding dimension"
    print(f"[download_model] ✓ Smoke test passed — embedding dim: {len(test_embedding)}")
    print(f"[download_model] ✓ Ready for offline use.")


if __name__ == "__main__":
    download()