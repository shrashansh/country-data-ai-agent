import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The country-related question to answer.")


class AskResponse(BaseModel):
    country: str
    fields: list[str]
    data: Dict[str, Any]
    answer: str


class ErrorResponse(BaseModel):
    error: str


class HealthResponse(BaseModel):
    status: str


_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph
    logger.info("Compiling agent graph…")
    from app.graph.agent_graph import get_agent_graph
    _graph = get_agent_graph()
    logger.info("Agent graph ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Country Data AI Agent",
    description="Ask natural language questions about countries and get structured answers.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="api/static"), name="static")
@app.get("/")
def homepage():
    return FileResponse("api/static/index.html")


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    """Return service liveness status."""
    return HealthResponse(status="ok")


@app.post(
    "/ask",
    response_model=AskResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["agent"],
)
def ask(request: AskRequest) -> JSONResponse:
    """Invoke the country information agent with a natural language question.

    The agent parses the question, fetches data from the REST Countries API,
    and returns a structured answer containing the country name, requested
    fields, the raw data, and a natural language summary.
    """
    logger.info("POST /ask — question: %r", request.question)

    initial_state = {
        "user_query": request.question,
        "country": None,
        "fields": [],
        "api_response": None,
        "normalized_data": None,
        "result": None,
        "error": None,
    }

    try:
        if _graph is None:
            logger.error("Agent graph not initialized")
            return JSONResponse(
                status_code=500,
                content={"error": "Agent not initialized"},
            )
            
        final_state = _graph.invoke(initial_state)
    except Exception as exc:
        logger.error("Unhandled exception during graph invocation: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {exc}"},
        )

    if final_state.get("error"):
        logger.warning("Graph returned an error: %s", final_state["error"])
        return JSONResponse(
            status_code=400,
            content={"error": final_state["error"]},
        )

    result = final_state.get("result")
    if not result:
        logger.error("Graph completed without an error but result is missing")
        return JSONResponse(
            status_code=500,
            content={"error": "Agent completed but produced no result."},
        )

    logger.info("POST /ask — success for country %r", result.get("country"))
    return JSONResponse(status_code=200, content=result)
