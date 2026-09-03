from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from sqlalchemy.orm import Session

from app.agent.orchestrator import VoiceAgent, create_provider
from app.api.auth import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.tools import tool_registry

router = APIRouter(prefix="/agent", tags=["Agent"])


@lru_cache
def get_agent() -> VoiceAgent:
    return VoiceAgent(create_provider(settings), tool_registry, max_tool_rounds=settings.agent_max_tool_rounds)


@router.post("/chat", response_model=AgentChatResponse)
def chat(request: AgentChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return get_agent().respond(db=db, user_id=current_user.id, message=request.message, session_id=request.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to reach Ollama. Start Ollama and make sure the configured model is installed.",
        ) from exc
