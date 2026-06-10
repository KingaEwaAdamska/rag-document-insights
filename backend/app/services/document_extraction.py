from pathlib import Path


def _extract_pdf(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(file_path: str) -> str:
    from docx import Document as DocxDocument

    doc = DocxDocument(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


def _extract_plain_text(file_path: str) -> str:
    with open(file_path, encoding="utf-8", errors="replace") as f:
        return f.read()


_EXTRACTORS = {
    ".pdf": _extract_pdf,
    ".docx": _extract_docx,
    ".txt": _extract_plain_text,
    ".md": _extract_plain_text,
}


def extract_text(file_path: str, mime_type: str) -> str:
    extension = Path(file_path).suffix.lower()
    extractor = _EXTRACTORS.get(extension)
    if extractor is None:
        raise ValueError(f"Unsupported file type: {extension}")
    return extractor(file_path)
