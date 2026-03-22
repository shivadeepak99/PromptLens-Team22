from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Dict, Any

from app.services.ml_service import ml_service
from app.agent.query_agent import run_agent_query, run_agent_query_with_trace

router = APIRouter()

class RecommendRequest(BaseModel):
    prompt_text: str

class ChatRequest(BaseModel):
    query: str

@router.post("/insights/recommend")
def recommend_prompt(req: RecommendRequest) -> Dict[str, Any]:
    # Integrates ML feature extraction and recommendations from our ML service
    return ml_service.recommend_improvements(req.prompt_text)

@router.post("/insights/chat")
def chat_with_agent(req: ChatRequest, debug: bool = Query(default=False)) -> Dict[str, Any]:
    """Chat endpoint to query the PromptLens agent for analytical insights."""
    if debug:
        answer, trace = run_agent_query_with_trace(req.query)
        return {"answer": answer, "trace": trace}
    answer = run_agent_query(req.query)
    return {"answer": answer}
