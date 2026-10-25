import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
WEEK2_APP = REPO_ROOT / "week2-realtime-data" / "app"

for path in (APP_DIR, WEEK2_APP, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent import SolarAgentDeps, solar_agent


logger = logging.getLogger(__name__)


app = FastAPI(
    title="SolarIQ API",
    description="AI-powered solar performance decision support",
    version="0.1.0",
)


class AssessmentRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "SolarIQ",
        "version": "0.1.0",
    }


@app.post("/assess")
async def assess(request: AssessmentRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question must not be blank.",
        )

    try:
        result = await solar_agent.run(
            question,
            deps=SolarAgentDeps(),
        )
        return result.output.model_dump(mode="json")
    except Exception:
        logger.exception("SolarIQ assessment failed")
        # Keep provider details and stack traces out of API responses.
        raise HTTPException(
            status_code=500,
            detail=(
                "SolarIQ could not complete the assessment. "
                "Check server logs."
            ),
        ) from None
