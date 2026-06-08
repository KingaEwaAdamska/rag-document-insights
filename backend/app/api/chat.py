import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db

# jeśli masz LangChain (opcjonalnie)
# from app.rag.chain import run_rag_chain

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    provider_id: str | None = None


class ChatResponse(BaseModel):
    content: str
    components: list | None = None


def run_chat(message: str, provider_id: str | None = None) -> dict:
    """
    Tu w przyszłości podłączasz LangChain:
    - RAG chain
    - retriever (Chroma / FAISS / PGVector)
    - tool calling
    """

    text = message.lower()

    if "code" in text:
        return {
            "content": "Here is a generated code example:",
            "components": [
                {
                    "type": "code_block",
                    "language": "python",
                    "code": "print('Hello from FastAPI + LangChain')",
                }
            ],
        }

    if "doc" in text or "document" in text:
        return {
            "content": "I found relevant document chunks:",
            "components": [
                {
                    "type": "citation_group",
                    "citations": [
                        {
                            "title": "Indexed Document",
                            "excerpt": "This is a retrieved chunk from vector database (RAG ready).",
                        }
                    ],
                }
            ],
        }

    if "action" in text:
        return {
            "content": "Here are suggested actions:",
            "components": [
                {
                    "type": "action_buttons",
                    "buttons": [
                        {"label": "Run analysis", "primary": True},
                        {"label": "Export results"},
                        {"label": "Save to workspace"},
                    ],
                }
            ],
        }

    return {
        "content": f"Processed message via FastAPI backend: {message}",
        "components": [
            {
                "type": "suggestion_chips",
                "chips": [
                    "Explain more",
                    "Give example",
                    "Show related docs",
                ],
            }
        ],
    }


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = run_chat(req.message, req.provider_id)
        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}",
        )
