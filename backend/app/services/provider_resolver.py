import enum
from pydantic import BaseModel
from app.models.llm_provider import LLMProviderConfig
from app.api.llm_providers import _fernet


class RuntimeProvider(BaseModel):
    id: str
    provider: str
    model: str
    api_key: str | None
    base_url: str | None


def decrypt_api_key(encrypted: str | None) -> str | None:
    if not encrypted:
        return None
    return _fernet().decrypt(encrypted.encode()).decode()


def resolve_runtime_provider(cfg: LLMProviderConfig) -> RuntimeProvider:
    return RuntimeProvider(
        id=cfg.id,
        provider=cfg.provider,
        model=cfg.model,
        api_key=decrypt_api_key(cfg.api_key_encrypted),
        base_url=cfg.base_url,
    )


ALLOWED_PROVIDERS = {"openai", "openrouter", "anthropic", "gemini", "ollama", "custom"}


def validate_provider(cfg: LLMProviderConfig):
    if normalize_provider(cfg) not in ALLOWED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {cfg.provider}")


def normalize_provider(cfg: LLMProviderConfig) -> str:
    if isinstance(cfg.provider, enum.Enum):
        return cfg.provider.value
    return str(cfg.provider).lower()

