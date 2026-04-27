import logging
import uuid
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
from backend.config import get_settings
from backend.models.models import ConfidenceResult, Segment, ScoringMethod
import asyncio

settings = get_settings()
logger = logging.getLogger("worker.confidence")

# Pydanctic schema for Gemini structured output
class ConfidenceScore(BaseModel):
    score: float
    key_phrases: list[str]
    hedging_phrases: list[str]

# Heuristic confidence scoring (fallback)
HEDGING_WORDS = [
    "believe", "expect", "anticipate", "hope", "approximately", "roughly",
    "around", "subject to", "may", "might", "could", "possibly", "potentially",
    "going forward", "we think", "we feel", "uncertain", "depends", "if",
    "assuming", "estimated", "projected", "target", "outlook", "cautious",
]

ASSERTIVE_WORDS = [
    "delivered", "achieved", "grew", "increased", "exceeded", "record",
    "committed", "will", "are confident", "have", "completed", "launched",
    "expanded", "secured", "generated", "returned", "gained", "won",
]

def _heuristic_confidence_score(text: str) -> ConfidenceScore:
    """
    Counts hedging vs assertive phrases in text and normalize to 0-10.
    Used as fallback when Gemini fails entirely.
    """
    text_lower = text.lower()

    hedging_found = [w for w in HEDGING_WORDS if w in text_lower]
    assertive_found = [w for w in ASSERTIVE_WORDS if w in text_lower]

    hedging_count = len(hedging_found)
    assertive_count = len(assertive_found)
    total_count = hedging_count + assertive_count

    if total_count == 0:
        score = 5.0
    else:
        score = round((assertive_count / total_count) * 10, 2)

    return ConfidenceScore(
        score=score,
        key_phrases=assertive_found,
        hedging_phrases=hedging_found,
    )

# Gemini call with tenacity 
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type((APIError,Exception)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_gemini(text: str) -> ConfidenceScore:
    """
    Calls Gemini with structured output enforced via response_schema
    to score confidence and hedging. Tenacity retries upto 3 times.
    """
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )

    prompt = (
    "You are analyzing a segment of an earnings call transcript. "
    "Score how confident and assertive the speaker sounds on a scale from 0 to 10, "
    "where 0 means extremely hedged and uncertain, and 10 means extremely assertive and certain. "
    "Identify the specific phrases that drove your score. "
    "key_phrases are assertive phrases that increased the score. "
    "hedging_phrases are uncertain or evasive phrases that decreased the score. "
    "Return between 2 and 10 phrases per category where present, or empty lists if none found.\n\n"
    f"Segment:\n{text}"
    )

    response = await client.aio.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ConfidenceScore,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(
                thinking_level="MINIMAL"
            ),
        ),
    )

    return response.parsed

# Per-segment handler

async def score_confidence_for_segment(
    segment: Segment,
) -> ConfidenceResult:
    """
    Scores confidencea and hedging for a single segment.
    Fallback to heuristic if Gemini fails.
    Returns an unsaved ConfidenceResult ORM object.
    """
    scoring_method = ScoringMethod.gemini
    
    try:
        result = await _call_gemini(segment.text)
        logger.info(
            f"[confidence] Segment {segment.id} | {segment.name}"
            f"Score: {result.score}"
            f"Key Phrases: {result.key_phrases}"
            f"Hedging Phrases: {result.hedging_phrases}"
        )
    
    except Exception as e:
        logger.error(
            f"[confidence] Error calling Gemini for segment {segment.id} | {segment.name} : {e}"
            f"Falling back to heuristic."
        )
        scoring_method = ScoringMethod.heuristic
        result = _heuristic_confidence_score(segment.text)
    
    return ConfidenceResult(
        segment_id=segment.id,
        score=result.score,
        scoring_method=scoring_method,
        key_phrases=result.key_phrases,
        hedging_phrases=result.hedging_phrases,
    )

# Public entry point
async def score_confidence_for_job(db: AsyncSession, job_id: uuid.UUID) -> list[ConfidenceResult]:
    """
    Fetches all segments for the job from DB, scores confidence on each.
    A failure on one segment does not block the rest.
    Returns a list of unsaved ConfidenceResult ORM objects.
    """
    result = await db.execute(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.order_index)
    )
    segments = result.scalars().all()
    results = await asyncio.gather(
        *[score_confidence_for_segment(segment) for segment in segments],
    )
    return list(results)