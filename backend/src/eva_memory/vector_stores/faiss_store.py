from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

import warnings

try:
    # Suppress SWIG deprecation warnings from FAISS
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPy.*")
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*swigvarlink.*")

    import faiss
except ImportError as exc:  # pragma: no cover - import error path
    raise ImportError(
        "Could not import faiss python package. "
        "Please install it with `pip install faiss-cpu` (or faiss-gpu for CUDA)."
    ) from exc


logger = logging.getLogger(__name__)


class FaissStore:
    """Per-user FAISS index manager using ID-mapped indices.

    This implementation:
    - Uses one index file per user.
    - Stores only vectors; all metadata lives in SQLite.
    - Supports true delete/update via IndexIDMap and `remove_ids`.
    """

    def __init__(
        self,
        base_dir: Path,
        distance_strategy: str = "l2",
        normalize_l2: bool = False,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.distance_strategy = distance_strategy
        self.normalize_l2 = normalize_l2

        # user_id -> faiss index
        self._indices: Dict[str, "faiss.Index"] = {}

    def _index_path(self, user_id: str) -> Path:
        return self.base_dir / f"user_{user_id}.faiss"

    def _create_index(self, dim: int) -> "faiss.Index":
        if self.distance_strategy.lower() in ("inner_product", "ip", "cosine"):
            base = faiss.IndexFlatIP(dim)
        else:
            base = faiss.IndexFlatL2(dim)

        # ID-mapped index so we can use our own faiss_id integers
        return faiss.IndexIDMap2(base)

    def _get_or_load_index(self, user_id: str, dim: int) -> "faiss.Index":
        if user_id in self._indices:
            return self._indices[user_id]

        path = self._index_path(user_id)
        if path.exists():
            index = faiss.read_index(str(path))
            self._indices[user_id] = index
            logger.info("Loaded FAISS index for user %s with %d vectors", user_id, index.ntotal)
            return index

        index = self._create_index(dim)
        self._indices[user_id] = index
        return index

    def _save_index(self, user_id: str) -> None:
        index = self._indices.get(user_id)
        if index is None:
            return
        path = self._index_path(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(path))

    def add(self, user_id: str, faiss_id: int, vector: List[float]) -> None:
        vec = np.asarray(vector, dtype=np.float32)
        if vec.ndim == 1:
            vec = vec.reshape(1, -1)

        if self.normalize_l2 and self.distance_strategy.lower() == "l2":
            faiss.normalize_L2(vec)

        index = self._get_or_load_index(user_id, dim=vec.shape[1])
        ids = np.asarray([faiss_id], dtype=np.int64)
        index.add_with_ids(vec, ids)
        self._save_index(user_id)

    def update(self, user_id: str, faiss_id: int, vector: List[float]) -> None:
        # Remove then re-add under the same id
        self.delete(user_id, faiss_id)
        self.add(user_id, faiss_id, vector)

    def delete(self, user_id: str, faiss_id: int) -> None:
        index = self._indices.get(user_id)
        if index is None:
            # Try to lazy-load; if file missing we are done
            path = self._index_path(user_id)
            if not path.exists():
                return
            index = faiss.read_index(str(path))
            self._indices[user_id] = index

        ids = np.asarray([faiss_id], dtype=np.int64)
        index.remove_ids(ids)
        self._save_index(user_id)

    def search(
        self,
        user_id: str,
        vector: List[float],
        k: int = 5,
    ) -> List[Tuple[int, float]]:
        """Return list of (faiss_id, score) for the user."""
        index = self._indices.get(user_id)
        if index is None:
            path = self._index_path(user_id)
            if not path.exists():
                return []
            index = faiss.read_index(str(path))
            self._indices[user_id] = index

        if index.ntotal == 0:
            return []

        vec = np.asarray(vector, dtype=np.float32)
        if vec.ndim == 1:
            vec = vec.reshape(1, -1)

        if self.normalize_l2 and self.distance_strategy.lower() == "l2":
            faiss.normalize_L2(vec)

        scores, ids = index.search(vec, k)
        result: List[Tuple[int, float]] = []
        for score, fid in zip(scores[0], ids[0]):
            if fid == -1:
                continue
            result.append((int(fid), float(score)))
        return result

    def reset_user(self, user_id: str) -> None:
        """Delete a user's index file and in-memory index."""
        if user_id in self._indices:
            del self._indices[user_id]
        path = self._index_path(user_id)
        if path.exists():
            path.unlink()

