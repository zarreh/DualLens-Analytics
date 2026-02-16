"""Load and chunk company AI-initiative PDF documents.

This module handles the first stage of the RAG ingestion pipeline:

1. Extract the knowledge-base ZIP archive.
2. Discover PDF files inside the extracted directory.
3. Split each PDF into overlapping text chunks using
   :class:`~langchain.text_splitter.RecursiveCharacterTextSplitter`
   with a ``tiktoken``-based length function.
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document

from duallens_analytics.config import PDF_DIR, ZIP_PATH

logger = logging.getLogger(__name__)


def extract_zip(zip_path: Path = ZIP_PATH, dest: Path = PDF_DIR) -> Path:
    """Extract the knowledge-base ZIP and return the directory with PDFs.

    If the archive contains a single top-level sub-folder the path of
    that sub-folder is returned; otherwise *dest* itself is returned.

    Args:
        zip_path: Path to the ``.zip`` archive (default: see
            :data:`~duallens_analytics.config.ZIP_PATH`).
        dest: Destination directory for extraction (default: see
            :data:`~duallens_analytics.config.PDF_DIR`).

    Returns:
        A :class:`~pathlib.Path` pointing to the directory that contains
        the extracted PDF files.
    """
    logger.info("Extracting ZIP %s → %s", zip_path, dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
        logger.debug("Extracted %d files from ZIP", len(zf.namelist()))

    # The zip may contain a sub-folder; find it
    subdirs = [p for p in dest.iterdir() if p.is_dir()]
    result = subdirs[0] if subdirs else dest
    logger.info("PDF directory resolved to %s", result)
    return result


def load_and_chunk(
    pdf_dir: Path | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    encoding_name: str = "cl100k_base",
) -> list[Document]:
    """Load all PDFs from *pdf_dir* and split into LangChain ``Document`` chunks.

    When *pdf_dir* is ``None`` the function calls :func:`extract_zip`
    first to unpack the default ZIP archive.

    Chunking parameters (*chunk_size*, *chunk_overlap*, *encoding_name*)
    can be overridden at runtime via Hydra config or directly.

    Args:
        pdf_dir: Directory containing ``.pdf`` files.  ``None`` triggers
            automatic extraction from the ZIP archive.
        chunk_size: Target number of tokens per chunk.
        chunk_overlap: Number of overlapping tokens between adjacent
            chunks to preserve context across boundaries.
        encoding_name: ``tiktoken`` encoding used to count tokens
            (e.g. ``"cl100k_base"``).

    Returns:
        A list of :class:`~langchain_core.documents.Document` objects,
        each representing one text chunk with metadata.
    """
    if pdf_dir is None:
        pdf_dir = extract_zip()

    logger.info(
        "Loading PDFs from %s (chunk_size=%d, overlap=%d, encoding=%s)",
        pdf_dir,
        chunk_size,
        chunk_overlap,
        encoding_name,
    )
    loader = PyPDFDirectoryLoader(str(pdf_dir))
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=encoding_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = loader.load_and_split(splitter)
    logger.info("Produced %d document chunks", len(chunks))
    return chunks
