import logging
import os

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.models.document import Document, DocumentStatus
from app.services import embeddings, vector_store
from app.services.chunking import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, chunk_text
from app.services.document_extraction import extract_text

logger = logging.getLogger(__name__)


def _process_document(db: Session, doc: Document) -> None:
    doc.status = DocumentStatus.INDEXING
    db.commit()

    try:
        text = extract_text(doc.file_path, doc.mime_type)
    except Exception as e:
        doc.status = DocumentStatus.FAILED
        doc.error_message = str(e)
        db.commit()
        return

    if not text.strip():
        doc.status = DocumentStatus.FAILED
        doc.error_message = (
            "No extractable text found (the document may be a "
            "scanned/image-based PDF)"
        )
        db.commit()
        return

    try:
        chunk_size = DEFAULT_CHUNK_SIZE
        chunk_overlap = DEFAULT_CHUNK_OVERLAP

        chunks = chunk_text(text, chunk_size, chunk_overlap)
        chunk_embeddings = embeddings.embed_texts(chunks)

        vector_store.delete_chunks(doc.id)
        vector_store.add_chunks(doc.id, chunks, chunk_embeddings, chunk_size, chunk_overlap)

        doc.chunk_count = len(chunks)
        doc.chunk_size = chunk_size
        doc.chunk_overlap = chunk_overlap
        doc.status = DocumentStatus.INDEXED
        doc.is_stale = False
        doc.error_message = None
        db.commit()
    except Exception as e:
        doc.status = DocumentStatus.FAILED
        doc.error_message = str(e)
        db.commit()


@celery_app.task(name="documents.index")
def index_document_task(document_id: str) -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        doc = (
            db.query(Document)
            .filter(Document.id == document_id, Document.deleted_at.is_(None))
            .first()
        )
        if doc is None:
            logger.info("Document %s not found or deleted, skipping indexing", document_id)
            return

        _process_document(db, doc)
    finally:
        db.close()


@celery_app.task(name="documents.reindex")
def reindex_document_task(document_id: str) -> None:
    index_document_task(document_id)


@celery_app.task(name="documents.delete")
def delete_document_task(document_id: str) -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc is None:
            logger.info("Document %s not found, nothing to delete", document_id)
            return

        try:
            vector_store.delete_chunks(doc.id)
        except Exception:
            logger.exception("Failed to delete vectors for document %s", doc.id)

        try:
            if doc.file_path and os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except Exception:
            logger.exception("Failed to delete file for document %s", doc.id)

        db.delete(doc)
        db.commit()
    finally:
        db.close()
