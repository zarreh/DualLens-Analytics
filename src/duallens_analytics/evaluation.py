"""LLM-as-Judge evaluation for RAG responses.

This module implements two evaluation dimensions for RAG quality:

- **Groundedness** – Is the answer fully supported by the retrieved
  context (no hallucination)?
- **Relevance** – Does the answer directly and completely address the
  user’s question?

Each evaluator sends the question, context, and answer to the LLM with
a specialised system prompt and parses the structured ``Score / Justification``
response into an :class:`EvalResult` dataclass.
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from duallens_analytics.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System messages for evaluators
# ---------------------------------------------------------------------------
GROUNDEDNESS_SYSTEM: str = """\
You are tasked with rating AI-generated answers to questions posed by users.
You will be presented a question, context used by the AI system to generate \
the answer and an AI-generated answer to the question.

In the input, the question will begin with ###Question, the context will begin \
with ###Context while the AI-generated answer will begin with ###Answer.

Evaluation criteria:
- Groundedness: Is the answer fully supported by the provided context?
- Avoid hallucination: Does the answer avoid adding information not present \
  in the context?

Provide:
1. A **score** from 1 (not grounded at all) to 5 (fully grounded).
2. A brief **justification** (2-3 sentences).

Format your response exactly as:
Score: <number>
Justification: <text>
"""

RELEVANCE_SYSTEM: str = """\
You are tasked with rating AI-generated answers to questions posed by users.
You will be presented a question, context used by the AI system to generate \
the answer and an AI-generated answer to the question.

In the input, the question will begin with ###Question, the context will begin \
with ###Context while the AI-generated answer will begin with ###Answer.

Evaluation criteria:
- Relevance: Does the answer directly address the question asked?
- Completeness: Does the answer cover the key aspects of the question?

Provide:
1. A **score** from 1 (not relevant) to 5 (highly relevant and complete).
2. A brief **justification** (2-3 sentences).

Format your response exactly as:
Score: <number>
Justification: <text>
"""
"""System prompt for the **relevance** evaluator."""

EVAL_USER_TEMPLATE: str = """\
###Question
{question}

###Context
{context}

###Answer
{answer}
"""
"""User-message template with ``{question}``, ``{context}``, and ``{answer}`` placeholders."""


@dataclass
class EvalResult:
    """Parsed result from an LLM-as-Judge evaluation.

    On instantiation the raw LLM response is automatically parsed to
    extract a numeric ``score`` and a textual ``justification``.

    Attributes:
        dimension: Evaluation dimension label (e.g. ``"Groundedness"``).
        raw_response: The full text returned by the evaluator LLM.
        score: Extracted integer score (1–5), or ``None`` if parsing
            failed.
        justification: Extracted justification text.
    """

    dimension: str
    raw_response: str
    score: int | None = None
    justification: str = ""

    def __post_init__(self) -> None:
        self._parse()

    def _parse(self) -> None:
        """Parse ``Score:`` and ``Justification:`` lines from *raw_response*."""
        for line in self.raw_response.splitlines():
            low = line.strip().lower()
            if low.startswith("score:"):
                with contextlib.suppress(ValueError, IndexError):
                    self.score = int(low.split(":", 1)[1].strip().split()[0])
            elif low.startswith("justification:"):
                self.justification = line.split(":", 1)[1].strip()


def _evaluate(
    system_msg: str,
    dimension: str,
    question: str,
    context: str,
    answer: str,
    settings: Settings,
) -> EvalResult:
    """Run a single LLM-as-Judge evaluation.

    This is the shared implementation behind :func:`evaluate_groundedness`
    and :func:`evaluate_relevance`.

    Args:
        system_msg: System prompt defining the evaluation criteria.
        dimension: Human-readable label (e.g. ``"Groundedness"``).
        question: The original user question.
        context: Concatenated context passages used for generation.
        answer: The AI-generated answer being evaluated.
        settings: Application settings (LLM model, temperature, etc.).

    Returns:
        An :class:`EvalResult` with the parsed score and justification.
    """
    llm = ChatOpenAI(
        model=settings.model,
        temperature=0,
        max_tokens=500,
        top_p=0.95,
        frequency_penalty=1.2,
    )
    prompt = (
        f"[INST]{system_msg}\n"
        f"user: {EVAL_USER_TEMPLATE.format(question=question, context=context, answer=answer)}"
        f"[/INST]"
    )
    logger.info("Running %s evaluation", dimension)
    resp = llm.invoke(prompt)
    result = EvalResult(dimension=dimension, raw_response=resp.content)
    logger.info("%s score: %s", dimension, result.score)
    return result


def evaluate_groundedness(
    question: str, context: str, answer: str, settings: Settings
) -> EvalResult:
    """Evaluate how well the *answer* is grounded in the *context*.

    A score of **5** means the answer is fully supported by the context
    with no hallucinated information.  A score of **1** indicates the
    answer contains significant unsupported claims.

    Args:
        question: The original user question.
        context: Concatenated retrieved context passages.
        answer: The AI-generated answer.
        settings: Application settings.

    Returns:
        An :class:`EvalResult` with the groundedness score.
    """
    return _evaluate(GROUNDEDNESS_SYSTEM, "Groundedness", question, context, answer, settings)


def evaluate_relevance(question: str, context: str, answer: str, settings: Settings) -> EvalResult:
    """Evaluate how relevant and complete the *answer* is to the *question*.

    A score of **5** means the answer directly addresses every aspect
    of the question.  A score of **1** means it is off-topic or
    incomplete.

    Args:
        question: The original user question.
        context: Concatenated retrieved context passages.
        answer: The AI-generated answer.
        settings: Application settings.

    Returns:
        An :class:`EvalResult` with the relevance score.
    """
    return _evaluate(RELEVANCE_SYSTEM, "Relevance", question, context, answer, settings)
