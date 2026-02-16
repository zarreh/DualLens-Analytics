"""ChromaDB vector-store management.

This module provides functions to **build**, **load**, and **query** a
ChromaDB vector store backed by OpenAI embeddings.  The store is
persisted to disk so subsequent application runs skip re-embedding.

Typical usage::

    store = get_or_create_vector_store(settings)
    retriever = get_retriever(store, k=5)
    docs = retriever.invoke("What AI projects is Google working on?")
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from duallens_analytics.config import CHROMA_DIR, Settings
from duallens_analytics.data_loader import load_and_chunk

logger = logging.getLogger(__name__)


def _embedding_fn(settings: Settings) -> OpenAIEmbeddings:
    """Return an :class:`~langchain_openai.OpenAIEmbeddings` instance.

    The embedding model name is read from
    :attr:`Settings.embedding_model`.

    Args:
        settings: Application settings containing the embedding model
            identifier.

    Returns:
        A configured ``OpenAIEmbeddings`` object.
    """
    return OpenAIEmbeddings(model=settings.embedding_model)


def build_vector_store(
    chunks: list[Document],
    settings: Settings,
    persist_dir: Path = CHROMA_DIR,
    collection_name: str = "AI_Initiatives",
) -> Chroma:
    """Create a ChromaDB collection from pre-chunked documents.

    Each document chunk is embedded via the configured OpenAI embedding
    model and stored in a local ChromaDB directory so that subsequent
    runs can load the collection without re-embedding.

    Args:
        chunks: Pre-split :class:`~langchain_core.documents.Document`
            objects produced by :func:`~duallens_analytics.data_loader.load_and_chunk`.
        settings: Application settings (used to select the embedding model).
        persist_dir: Filesystem path where ChromaDB persists its data.
        collection_name: Logical name of the collection inside ChromaDB.

    Returns:
        A :class:`~langchain_chroma.Chroma` instance
        backed by the newly created collection.
    """
    logger.info(
        "Building vector store: %d chunks → collection=%s, persist=%s",
        len(chunks),
        collection_name,
        persist_dir,
    )
    persist_dir.mkdir(parents=True, exist_ok=True)
    return Chroma.from_documents(
        chunks,
        _embedding_fn(settings),
        collection_name=collection_name,
        persist_directory=str(persist_dir),
    )


def load_vector_store(
    settings: Settings,
    persist_dir: Path = CHROMA_DIR,
    collection_name: str = "AI_Initiatives",
) -> Chroma:
    """Load an already-persisted ChromaDB collection from disk.

    This skips the embedding step entirely by reading the existing
    SQLite database that ChromaDB maintains inside *persist_dir*.

    Args:
        settings: Application settings (needed for the embedding function
            so that query-time embeddings match the stored ones).
        persist_dir: Filesystem path where ChromaDB persists its data.
        collection_name: Logical name of the collection inside ChromaDB.

    Returns:
        A :class:`~langchain_chroma.Chroma` instance.
    """
    logger.info("Loading existing vector store: collection=%s", collection_name)
    return Chroma(
        collection_name=collection_name,
        embedding_function=_embedding_fn(settings),
        persist_directory=str(persist_dir),
    )


def collection_exists(
    persist_dir: Path = CHROMA_DIR,
    collection_name: str = "AI_Initiatives",
) -> bool:
    """Check whether a persisted ChromaDB collection already exists.

    The heuristic inspects the presence of ``chroma.sqlite3`` inside
    *persist_dir*.

    Args:
        persist_dir: Directory that ChromaDB uses for persistence.
        collection_name: Unused at present but kept for future
            multi-collection support.

    Returns:
        ``True`` if the SQLite database file is present.
    """
    chroma_sqlite = persist_dir / "chroma.sqlite3"
    exists = chroma_sqlite.is_file()
    logger.debug(
        "Checking persisted collection (path=%s, exists=%s)",
        chroma_sqlite,
        exists,
    )
    return exists


def get_or_create_vector_store(
    settings: Settings,
    persist_dir: Path = CHROMA_DIR,
    collection_name: str | None = None,
) -> Chroma:
    """Load an existing vector store or ingest from PDFs if none is found.

    This is the recommended entry-point for application code.  It
    encapsulates the *load-or-build* logic so callers do not need to
    manage ingestion themselves.

    If the ChromaDB data directory already exists on disk the documents
    are **not** re-embedded, saving time and API credits.

    Args:
        settings: Application settings (embedding model, chunking params,
            collection name).
        persist_dir: Filesystem path for ChromaDB persistence.
        collection_name: Override for the collection name. Defaults to
            ``settings.collection_name``.

    Returns:
        A :class:`~langchain_chroma.Chroma` instance
        ready for retrieval.
    """
    collection_name = collection_name or settings.collection_name

    if collection_exists(persist_dir, collection_name):
        logger.info("Persisted vector store found – loading from disk")
        return load_vector_store(settings, persist_dir, collection_name)

    logger.info("No persisted vector store found – ingesting from PDFs")
    chunks = load_and_chunk(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        encoding_name=settings.encoding_name,
    )
    return build_vector_store(chunks, settings, persist_dir, collection_name)


def get_retriever(
    store: Chroma,
    k: int = 10,
    search_type: str = "similarity",
) -> VectorStoreRetriever:
    """Create a LangChain retriever over the given vector store.

    Args:
        store: A ChromaDB-backed vector store.
        k: Number of top-matching documents to return per query.
        search_type: Retrieval strategy — ``"similarity"`` (cosine) or
            ``"mmr"`` (maximal marginal relevance).

    Returns:
        A :class:`~langchain_core.vectorstores.VectorStoreRetriever`
        that can be called with ``retriever.invoke(question)``.
    """
    logger.info("Creating retriever (search_type=%s, k=%d)", search_type, k)
    return store.as_retriever(search_type=search_type, search_kwargs={"k": k})
