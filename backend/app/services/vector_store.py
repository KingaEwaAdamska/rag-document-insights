import os

from app.services.chunking import CHUNK_STRATEGY

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
COLLECTION_NAME = "documents"

_client = None


def get_chroma_client():
    global _client
    if _client is None:
        import chromadb

        if os.getenv("CHROMA_CLIENT_MODE") == "ephemeral":
            _client = chromadb.EphemeralClient()
        else:
            _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return _client


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def add_chunks(
    document_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    if not chunks:
        return

    collection = get_collection()
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "chunk_index": i,
            "chunk_size_config": chunk_size,
            "chunk_overlap_config": chunk_overlap,
            "strategy": CHUNK_STRATEGY,
        }
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def delete_chunks(document_id: str) -> None:
    collection = get_collection()
    collection.delete(where={"document_id": document_id})
