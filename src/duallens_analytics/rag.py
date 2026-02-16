"""RAG pipeline – retrieval + LLM generation.

This module implements the core Retrieval-Augmented Generation loop:

1. Accept a user question.
2. Retrieve the top-*k* relevant document chunks from the ChromaDB
   vector store.
3. Assemble a prompt that injects the retrieved context.
4. Invoke the Chat LLM and return the generated answer together with
   the source excerpts.
"""

from __future__ import annotations

import logging

from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI

from duallens_analytics.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
QNA_SYSTEM_MESSAGE: str = """\
You are an assistant specialised in reviewing AI initiatives of companies and \
providing accurate answers based on the provided context.

User input will include all the context you need to answer their question.
This context will always begin with the token: ###Context.
The context contains references to specific AI initiatives, projects, or \
programmes of companies relevant to the user's question.

Instructions:
- Answer ONLY based on the context provided.
- If the context is insufficient, clearly state that.
- Your response should be well-structured and concise.
"""
"""System message instructing the LLM to answer only from provided context."""

QNA_USER_TEMPLATE: str = """\
###Context
Here are some documents that are relevant to the question mentioned below.
{context}

###Question
{question}
"""
"""User-message template with ``{context}`` and ``{question}`` placeholders."""


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------
def get_llm(settings: Settings) -> ChatOpenAI:
    """Return a configured :class:`~langchain_openai.ChatOpenAI` instance.

    All LLM hyper-parameters (model, temperature, max_tokens, etc.) are
    read from the supplied :class:`~duallens_analytics.config.Settings`.

    Args:
        settings: Application settings.

    Returns:
        A ready-to-invoke ``ChatOpenAI`` object.
    """
    logger.debug(
        "Creating ChatOpenAI: model=%s, temp=%.2f, max_tokens=%d",
        settings.model,
        settings.temperature,
        settings.max_tokens,
    )
    return ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        top_p=settings.top_p,
        frequency_penalty=settings.frequency_penalty,
    )


# ---------------------------------------------------------------------------
# Core RAG function
# ---------------------------------------------------------------------------
def query_rag(
    question: str,
    retriever: VectorStoreRetriever,
    settings: Settings,
) -> tuple[str, list[str]]:
    """Execute the full RAG loop: retrieve context then generate an answer.

    Args:
        question: Natural-language question from the user.
        retriever: A LangChain retriever backed by the ChromaDB vector
            store (see :func:`~duallens_analytics.vector_store.get_retriever`).
        settings: Application settings forwarded to :func:`get_llm`.

    Returns:
        A tuple of ``(answer_text, source_excerpts)`` where
        *source_excerpts* is a list of the raw ``page_content`` strings
        from the retrieved document chunks.
    """
    logger.info("RAG query: %s", question[:120])
    docs = retriever.invoke(question)
    context_parts = [d.page_content for d in docs]
    logger.debug("Retrieved %d context chunks", len(context_parts))
    context = ". ".join(context_parts)

    prompt = (
        f"[INST]{QNA_SYSTEM_MESSAGE}\n"
        f"user: {QNA_USER_TEMPLATE.format(context=context, question=question)}"
        f"[/INST]"
    )

    llm = get_llm(settings)
    logger.debug("Invoking LLM for RAG answer")
    resp = llm.invoke(prompt)
    logger.info("RAG answer generated (%d chars)", len(resp.content))
    return resp.content, context_parts
