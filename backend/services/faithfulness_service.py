import logging
import uuid
import asyncio
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
from backend.config import get_settings
from backend.models.models import Summary, FaithfulnessStatus, Segment

settings = get_settings()
logger = logging.getLogger("worker.faithfulness")

VERIFIED_THRESHOLD = 0.8
PARTIAL_THRESHOLD = 0.5

# Pydantic schema for Gemini structured output
class FaithfulnessResult(BaseModel):
    score: float
    flagged_claims: list[str]

# Gemini call with tenacity retry logic
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type((APIError,Exception)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_gemini(summary_text: str, segment_text: str) -> FaithfulnessResult:
    """
    Calls Gemini to score how faithfully the summary represents
    the source segment. Returns a score between 0 and 1 and a list
    of specific claims in the summary that could not be verified
    against the source text.
    """
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
    
    prompt = (
        "You are a fact-checking assistant reviewing an AI-generated summary "
        "of an earnings call transcript segment.\n\n"
        "Your task is to score how faithfully the summary represents the source text "
        "on a scale from 0.0 to 1.0, where:\n"
        "- 1.0 means every claim in the summary is directly supported by the source\n"
        "- 0.5 means some claims are supported but others are missing or imprecise\n"
        "- 0.0 means the summary contains claims not found in or contradicted by the source\n\n"
        "Also list any specific claims from the summary that you could not verify "
        "in the source text. If all claims are verified, return an empty list.\n\n"
        f"Source segment:\n{segment_text}\n\n"
        f"Summary to verify:\n{summary_text}"
    )

    
    response = await client.aio.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FaithfulnessResult,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(
                thinking_level="MINIMAL"
            ),
        ),
    )

    return response.parsed

# status resolution

def _resolve_status(score: float) -> FaithfulnessStatus:
    """
    Resolve faithfulness status based on score.
    """
    if score >= VERIFIED_THRESHOLD:
        return FaithfulnessStatus.verified
    elif score >= PARTIAL_THRESHOLD:
        return FaithfulnessStatus.partially_verified
    else:
        return FaithfulnessStatus.unverified

# Per-summary handler
async def check_faithfulness_for_summary(
    segment: Segment,
    summary: Summary,
) -> None:
    """
    Checks faithfulness of a summary against its source segment.
    Updates the Summary ORM object in place with score and status
    and flagged claims. Never raises always continues.
    """
    try:
        result = await _call_gemini(summary.text, segment.text)
        score = max(0.0, min(1.0, result.score))
        status = _resolve_status(score)
        
        summary.faithfulness_score = score
        summary.faithfulness_status = status
        summary.flagged_claims = result.flagged_claims if result.flagged_claims else None

        logger.info(
            f"[faithfulness] Segment {segment.id} | {segment.name}"
            f" score: {score:.2f} status: {status.value}"
            f" flagged claims: {len(result.flagged_claims) if result.flagged_claims else 0}"
        )
    except Exception as e:
        logger.error(
            f"[faithfulness] Error calling Gemini for segment {segment.id} | {segment.name} : {e}"
            f"Leaving unverified."
        )
        summary.faithfulness_score = None
        summary.faithfulness_status = FaithfulnessStatus.unverified
        summary.flagged_claims = None
    
# Public entry point
async def run_faithfulness_checks_for_job(db: AsyncSession, job_id: uuid.UUID) -> None:
    """
    Fetches all summaries for the job from DB, checks faithfulness for each.
    A failure on one summary does not block the rest.
    """
    result = await db.execute(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.order_index).options(selectinload(Segment.summary))
    )
    segments = result.scalars().all()
    await asyncio.gather(
        *[check_faithfulness_for_summary(segment, segment.summary) for segment in segments],
    )
