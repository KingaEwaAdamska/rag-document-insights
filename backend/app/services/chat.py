from app.services.provider import get_provider
from app.services.provider_resolver import resolve_runtime_provider
from app.services.llm import run_llm
from app.services.rag import run_rag


def build_components(message: str, content: str, rag_context: str | None):
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

    return components


def handle_chat(req, db):
    cfg = get_provider(db, req.provider_id)

    runtime = resolve_runtime_provider(cfg)

    rag_context = run_rag(req.message)

    content = run_llm(runtime, req.message, rag_context)

    return {
        "content": content,
        "components": build_components(req.message, content, rag_context),
    }
