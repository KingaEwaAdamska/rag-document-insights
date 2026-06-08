from fastapi import APIRouter, Depends, HTTPException
import logging
import traceback
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.chat import handle_chat

router = APIRouter(prefix="/chat", tags=["chat"])

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    provider_id: str | None = None


class ChatResponse(BaseModel):
    content: str
    components: list | None = None


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = handle_chat(req, db)
        return ChatResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error("CHAT ERROR")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
