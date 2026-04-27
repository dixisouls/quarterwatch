import logging
import httpx
from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger("worker.transcript")

FMP_BASE_URL = "https://financialmodelingprep.com/stable/earning-call-transcript"

QUARTER_MAP = {
    "Q1": 1,
    "Q2": 2,
    "Q3": 3,
    "Q4": 4,
}

async def fetch_transcript(ticker: str, quarter: str, year: int) -> str | None:
    """
    Fetch all earnings call transcript from FMP.

    Returns the raw transcript text if found, or None if not found or if
    the API call fails. Never raises, always returns or returns None.
    """
    quarter_int = QUARTER_MAP.get(quarter)
    if quarter_int is None:
        logger.error(f"[transcript] Invalid quarter value: {quarter}")
        return None

    params = {
        "symbol": ticker,
        "year": year,
        "quarter": quarter_int,
        "apikey": settings.fmp_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(FMP_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list) or len(data) == 0:
                logger.warning(f"[transcript] No transcript found for {ticker} {quarter} {year}")
                return None
            
            transcript_entry = data[0]
            content = transcript_entry.get("content") or transcript_entry.get("transcript")
            
            if not content or not content.strip():
                logger.warning(
                    f"[transcript] Empty transcript content for {ticker} {quarter} {year}"
                )
                return None
            
            logger.info(
                f"[transcript] Successfully fetched transcript for {ticker} {quarter} {year}"
                f"({len(content)} characters)"
            )
            return content.strip()
    except httpx.HTTPStatusError as e:
        logger.error(
            f"[transcript] HTTP error fetching transcript for {ticker} {quarter} {year}:"
            f"{e.response.status_code} {e.response.text}"
        )
        return None
    except httpx.RequestError as e:
        logger.error(
            f"[transcript] Network error fetching transcript for {ticker} {quarter} {year}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"[transcript] Unexpected error fetching transcript for {ticker} {quarter} {year}: {e}"
        )
        return None
            