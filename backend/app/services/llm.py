from app.services.provider_resolver import (
    resolve_runtime_provider,
    validate_provider,
    build_llm,
)


def run_llm(runtime, message, rag_context):
    final_input = message

    if rag_context:
        final_input = f"Context:\n{rag_context}\n\nUser:\n{message}"

    response = build_llm(runtime).invoke(final_input)

    return response.content
