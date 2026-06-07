import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from app.api import documents, llm_providers

app = FastAPI(title="RAG Document Insights", version="0.1.0")

app.include_router(documents.router, prefix="/api/v1")
app.include_router(llm_providers.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
