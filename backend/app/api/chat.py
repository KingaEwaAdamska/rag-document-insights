from fastapi import APIRouter, Depends, HTTPException
import os
import logging
import traceback
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.llm_provider import LLMProviderConfig

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from app.services.provider_resolver import (
    resolve_runtime_provider,
    validate_provider,
    RuntimeProvider,
)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    provider_id: str | None = None


class ChatResponse(BaseModel):
    content: str
    components: list | None = None


def get_provider(db: Session, provider_id: str | None) -> LLMProviderConfig:
    if provider_id:
        cfg = (
            db.query(LLMProviderConfig)
            .filter(LLMProviderConfig.id == provider_id)
            .first()
        )

        if not cfg:
            raise HTTPException(status_code=404, detail="Provider not found")
        return cfg

    cfg = (
        db.query(LLMProviderConfig).filter(LLMProviderConfig.is_active == True).first()
    )

    if not cfg:
        raise HTTPException(status_code=400, detail="No active provider configured")

    return cfg


def run_rag_if_needed(message: str) -> str | None:
    if "doc" in message.lower():
        return "Retrieved context from vector DB"
    return None


def build_llm(runtime):
    if runtime.provider == "ollama":
        return ChatOllama(
            model=runtime.model,
            base_url=runtime.base_url or "http://localhost:11434",
            temperature=0.7,
        )

    if not runtime.api_key:
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_FALLBACK_KEY"),
        )

    if runtime.provider in ["openai", "openrouter"]:
        return ChatOpenAI(
            model=runtime.model,
            api_key=runtime.api_key,
            base_url=runtime.base_url if runtime.provider == "openrouter" else None,
            temperature=0.7,
        )

    if runtime.provider == "anthropic":
        return ChatAnthropic(
            model=runtime.model,
            api_key=runtime.api_key,
            temperature=0.7,
        )

    if runtime.provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=runtime.model,
            google_api_key=runtime.api_key,
            temperature=0.7,
        )

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported provider: {runtime.provider}",
    )


def run_chat(message: str, cfg: LLMProviderConfig) -> dict:
    runtime = resolve_runtime_provider(cfg)

    try:
        validate_provider(cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    llm = build_llm(runtime)

    rag_context = run_rag_if_needed(message)

    final_input = message
    if rag_context:
        final_input = f"Context:\n{rag_context}\n\nUser:\n{message}"

    try:
        response = llm.invoke(final_input)
        content = response.content

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {str(e)}")

    text = message.lower()
    components = []

    if "code" in text:
        components.append(
            {
                "type": "code_block",
                "language": "python",
                "code": content,
            }
        )

    elif "doc" in text:
        components.append(
            {
                "type": "citation_group",
                "citations": [
                    {
                        "title": "RAG Source",
                        "excerpt": rag_context or "No context",
                    }
                ],
            }
        )

    elif "action" in text:
        components.append(
            {
                "type": "action_buttons",
                "buttons": [
                    {"label": "Run analysis", "primary": True},
                    {"label": "Export"},
                    {"label": "Save"},
                ],
            }
        )

    else:
        components.append(
            {
                "type": "suggestion_chips",
                "chips": [
                    "Explain more",
                    "Give example",
                    "Show docs",
                ],
            }
        )

    return {
        "content": content,
        "components": components,
    }


logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        cfg = get_provider(db, req.provider_id)

        result = run_chat(req.message, cfg)
        return ChatResponse(**result)

    except Exception as e:
        logger.error("CHAT ERROR")
        traceback.print_exc()  # 🔥 KLUCZOWE

        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {str(e)}",
        )

