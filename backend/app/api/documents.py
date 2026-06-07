import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


# TODO: handle file uploads and storage properly - add celery worker for indexing and cleaning up old files etc
@router.post("", response_model=DocumentResponse, status_code=201)
def create_document(body: DocumentCreate, db: Session = Depends(get_db)):
    stored_name = f"{uuid.uuid4()}_{body.original_filename}"
    doc = Document(
        original_filename=body.original_filename,
        stored_filename=stored_name,
        file_path=f"data/uploads/{stored_name}",
        file_size=body.file_size,
        mime_type=body.mime_type,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
