# ingestion/document_registry.py
"""
Persistent document-level metadata registry.

Stored at: data/document_registry.json
Each entry records ingestion metadata for one source document.

Structure:
    {
      "policy.pdf": {
        "source_file":       "policy.pdf",
        "file_type":         "pdf",
        "file_size_bytes":   45231,
        "file_size_display": "44.2 KB",
        "upload_timestamp":  "2026-06-18T10:30:00",
        "chunk_count":       14,
        "ingestion_id":      "a3f9c2b1"
      },
      ...
    }

This file is independent of ChromaDB — it is not cleared by 'make clean-db'.
Call sync_with_store() to remove registry entries for deleted documents.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


REGISTRY_PATH = Path("data/document_registry.json")


class DocumentRegistry:
    """
    File-backed registry of document ingestion metadata.
    Thread-safe for single-process use (reads/writes full JSON on every operation).
    """

    def __init__(self, path: str = None):
        self._path = Path(path) if path else REGISTRY_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({})

    # ── Core operations ───────────────────────────────────────────────

    def _read(self) -> Dict:
        try:
            with open(self._path) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, data: Dict) -> None:
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Human-readable file size: '44.2 KB', '1.3 MB'."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 ** 2):.1f} MB"

    def register(
        self,
        source_file: str,
        file_path: str,
        chunk_count: int,
    ) -> dict:
        """
        Record a document ingestion.

        Args:
            source_file: Filename (e.g., 'policy.pdf')
            file_path:   Full path to original file (for size/type metadata)
            chunk_count: Number of chunks indexed into ChromaDB

        Returns:
            The document info dict that was stored.
        """
        p = Path(file_path)
        size_bytes = p.stat().st_size if p.exists() else 0

        entry = {
            "source_file":       source_file,
            "file_type":         p.suffix.lstrip(".").lower() or "unknown",
            "file_size_bytes":   size_bytes,
            "file_size_display": self._format_size(size_bytes),
            "upload_timestamp":  datetime.now().isoformat(timespec="seconds"),
            "chunk_count":       chunk_count,
            "ingestion_id":      uuid.uuid4().hex[:8],
        }

        data = self._read()
        data[source_file] = entry
        self._write(data)

        logger.info(
            f"Registered '{source_file}': "
            f"{chunk_count} chunks, {entry['file_size_display']}"
        )
        return entry

    def get(self, source_file: str) -> Optional[dict]:
        """Return the registry entry for one document, or None."""
        return self._read().get(source_file)

    def list_all(self) -> List[dict]:
        """Return all registry entries, sorted by upload_timestamp descending."""
        data = self._read()
        entries = list(data.values())
        entries.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
        return entries

    def remove(self, source_file: str) -> bool:
        """Remove a document from the registry. Returns True if it existed."""
        data = self._read()
        if source_file in data:
            del data[source_file]
            self._write(data)
            logger.info(f"Removed '{source_file}' from document registry.")
            return True
        return False

    def sync_with_store(self, active_sources: List[str]) -> int:
        """
        Remove registry entries for documents that no longer exist in ChromaDB.
        Called after a manual store clear or batch deletion.

        Args:
            active_sources: List of source_file values currently in ChromaDB

        Returns:
            Number of stale entries removed.
        """
        data    = self._read()
        stale   = [k for k in data if k not in active_sources]
        removed = 0
        for key in stale:
            del data[key]
            removed += 1

        if stale:
            self._write(data)
            logger.info(f"Registry sync: removed {removed} stale entries {stale}")

        return removed

    def __len__(self) -> int:
        return len(self._read())
