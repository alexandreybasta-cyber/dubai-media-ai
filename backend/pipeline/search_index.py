"""
Stage 6: Search Index
FAISS-based vector search index with DashScope text embeddings.
"""

import asyncio
import json
import logging
import os
import pickle
from typing import List, Optional

import httpx
import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1024  # text-embedding-v3 dimension
INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "search_index")


class SearchIndex:
    """FAISS-based search index with DashScope text embeddings."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "text-embedding-v3",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        index_dir: str = INDEX_DIR,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.index_dir = index_dir
        self.index = None
        self.metadata: List[dict] = []  # parallel list of metadata for each vector

        os.makedirs(self.index_dir, exist_ok=True)
        self._load_index()

    def _load_index(self):
        """Load existing FAISS index and metadata from disk."""
        index_path = os.path.join(self.index_dir, "faiss.index")
        meta_path = os.path.join(self.index_dir, "metadata.pkl")

        try:
            import faiss

            if os.path.exists(index_path) and os.path.exists(meta_path):
                self.index = faiss.read_index(index_path)
                with open(meta_path, "rb") as f:
                    self.metadata = pickle.load(f)
                logger.info(
                    "Loaded search index with %d vectors", self.index.ntotal
                )
            else:
                self.index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner product (cosine after normalization)
                self.metadata = []
                logger.info("Created new FAISS index")
        except ImportError:
            logger.warning("faiss-cpu not installed, search will be unavailable")
            self.index = None
            self.metadata = []
        except Exception as e:
            logger.error("Failed to load search index: %s", e)
            import faiss
            self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
            self.metadata = []

    def _save_index(self):
        """Persist FAISS index and metadata to disk."""
        if self.index is None:
            return

        try:
            import faiss

            index_path = os.path.join(self.index_dir, "faiss.index")
            meta_path = os.path.join(self.index_dir, "metadata.pkl")
            faiss.write_index(self.index, index_path)
            with open(meta_path, "wb") as f:
                pickle.dump(self.metadata, f)
            logger.info("Saved search index with %d vectors", self.index.ntotal)
        except Exception as e:
            logger.error("Failed to save search index: %s", e)

    async def add_video(self, video_id: str, segments: list):
        """
        Add video segments to search index with embeddings.

        Args:
            video_id: Unique identifier for the video.
            segments: List of dicts, each with at least 'description' or 'text',
                      and optionally 'timestamp', 'scene_type', etc.
        """
        if self.index is None:
            logger.warning("No FAISS index available, skipping add_video")
            return

        if not segments:
            logger.info("No segments to index for video %s", video_id)
            return

        # Build texts to embed
        texts = []
        metas = []
        for seg in segments:
            text = (
                seg.get("description_en")
                or seg.get("description")
                or seg.get("text")
                or ""
            )
            if not text:
                continue
            texts.append(text)
            metas.append({
                "video_id": video_id,
                "timestamp": seg.get("timestamp", seg.get("start_time", 0)),
                "description": text,
                "scene_type": seg.get("scene_type", ""),
                "type": seg.get("type", "scene"),
            })

        if not texts:
            return

        # Get embeddings in batches (max 25 per call)
        all_embeddings = []
        batch_size = 25
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await self._get_embeddings(batch)
            if embeddings is not None:
                all_embeddings.extend(embeddings)
            else:
                # Use zero vectors as fallback
                all_embeddings.extend([np.zeros(EMBEDDING_DIM)] * len(batch))

        if not all_embeddings:
            return

        # Normalize and add to index
        vectors = np.array(all_embeddings, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vectors = vectors / norms

        self.index.add(vectors)
        self.metadata.extend(metas)
        self._save_index()

        logger.info("Added %d segments for video %s to search index", len(texts), video_id)

    async def search(self, query: str, top_k: int = 5) -> list:
        """
        Search for videos/segments matching a natural language query.

        Args:
            query: Natural language search query.
            top_k: Number of results to return.

        Returns:
            List of dicts with video_id, timestamp, description, score.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Search index is empty or unavailable")
            return []

        embeddings = await self._get_embeddings([query])
        if embeddings is None or len(embeddings) == 0:
            return []

        query_vec = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(query_vec, axis=1, keepdims=True)
        norms[norms == 0] = 1
        query_vec = query_vec / norms

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append({
                "video_id": meta["video_id"],
                "timestamp": meta["timestamp"],
                "description": meta["description"],
                "scene_type": meta.get("scene_type", ""),
                "score": float(score),
            })

        return results

    async def _get_embeddings(self, texts: list) -> Optional[List[list]]:
        """Get text embeddings from DashScope API."""
        if not self.api_key:
            logger.warning("No API key for embeddings")
            return None

        endpoint = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

                embeddings = []
                for item in sorted(data.get("data", []), key=lambda x: x.get("index", 0)):
                    embeddings.append(item["embedding"])
                return embeddings

            except httpx.HTTPStatusError as e:
                logger.error(
                    "Embedding API error (attempt %d/3): %s – %s",
                    attempt + 1, e.response.status_code, e.response.text[:500],
                )
            except httpx.RequestError as e:
                logger.error(
                    "Embedding request error (attempt %d/3): %s",
                    attempt + 1, e,
                )
            except Exception as e:
                logger.error(
                    "Embedding unexpected error (attempt %d/3): %s",
                    attempt + 1, e,
                )

            await asyncio.sleep(2 ** attempt)

        return None
