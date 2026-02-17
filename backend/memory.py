"""Long-term memory system using ChromaDB + markdown files."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages conversation memory with ChromaDB vectors and markdown files."""

    def __init__(self) -> None:
        self._collection = None

    def _ensure_loaded(self) -> None:
        if self._collection is not None:
            return
        logger.info("Initializing ChromaDB...")
        import chromadb
        client = chromadb.PersistentClient(path=str(settings.chromadb_dir))
        self._collection = client.get_or_create_collection(
            name="conversations",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB initialized with %d entries.", self._collection.count())

    def _store_sync(self, user_text: str, assistant_text: str, tool_annotations: str = "") -> None:
        """Store a conversation exchange in both markdown and ChromaDB."""
        self._ensure_loaded()
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        # Append to markdown file
        md_path = settings.conversations_dir / f"{date_str}.md"
        is_new = not md_path.exists()

        with open(md_path, "a", encoding="utf-8") as f:
            if is_new:
                f.write(f"# {date_str}\n\n")
            f.write(f"## {time_str}\n\n")
            f.write(f"**User:** {user_text}\n\n")
            assistant_content = assistant_text
            if tool_annotations:
                assistant_content = f"{assistant_text} {tool_annotations}"
            f.write(f"**Assistant:** {assistant_content}\n\n---\n\n")

        # Store in ChromaDB for semantic retrieval
        doc = f"User: {user_text}\nAssistant: {assistant_text}"
        doc_id = f"{date_str}_{time_str}_{hash(doc) & 0xFFFFFFFF:08x}"

        try:
            self._collection.add(
                documents=[doc],
                metadatas=[{"date": date_str, "time": time_str}],
                ids=[doc_id],
            )
        except Exception as e:
            logger.warning("ChromaDB store failed: %s", e)

    def _retrieve_sync(self, query: str, n_results: int = 3) -> str:
        """Retrieve relevant past conversations as formatted context string."""
        self._ensure_loaded()

        if self._collection.count() == 0:
            return ""

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, self._collection.count()),
            )
        except Exception as e:
            logger.warning("ChromaDB retrieval failed: %s", e)
            return ""

        if not results or not results.get("documents"):
            return ""

        docs = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)

        if not docs:
            return ""

        lines = []
        for doc, meta in zip(docs, metadatas):
            date = meta.get("date", "unknown date")
            lines.append(f"[{date}] {doc}")

        return "\n\n".join(lines)

    def _get_today_context_sync(self) -> str:
        """Get today's conversation history from the markdown file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        md_path = settings.conversations_dir / f"{date_str}.md"

        if not md_path.exists():
            return ""

        content = md_path.read_text(encoding="utf-8")
        # Truncate if too long (keep last ~2000 chars)
        if len(content) > 2000:
            content = "...\n" + content[-2000:]
        return content

    async def store(self, user_text: str, assistant_text: str, tool_annotations: str = "") -> None:
        await asyncio.to_thread(self._store_sync, user_text, assistant_text, tool_annotations)

    async def retrieve(self, query: str, n_results: int = 3) -> str:
        return await asyncio.to_thread(self._retrieve_sync, query, n_results)

    async def get_today_context(self) -> str:
        return await asyncio.to_thread(self._get_today_context_sync)
