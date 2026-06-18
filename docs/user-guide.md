# User Guide

## Uploading documents

1. Open the **Documents** page.
2. Drag in or pick a file — PDF, DOCX, TXT, or MD.
3. The file is checked by its actual content (not just its extension) and rejected
   if it doesn't match. Accepted files start in `pending` status, then move to
   `indexing` and finally `indexed` once chunked and embedded.
4. If indexing fails, the document shows `failed` with an error message — fix the
   underlying issue (e.g. corrupt file, empty text extracted from a scanned PDF) and
   hit **Reindex**.

Each document tracks its own chunk size/overlap. If you change the global chunking
defaults later, already-indexed documents are marked **stale** — reindex them to pick
up the new settings.

## Chatting

1. Open the **Chat** page, pick a provider (see below) if you have more than one.
2. Type a question and send it. The assistant decides on its own whether it needs to
   search your documents — you'll see live "Searching documents…" style steps while
   it works, not just a final answer.
3. Answers that were grounded in a document show a **retrieval panel** with the
   matching excerpts and their source document.
4. After document-based answers, the assistant often suggests 2-3 follow-up
   questions as clickable chips.
5. Conversations are listed in the sidebar and persist — reopen one anytime, or
   delete it.

## Managing LLM providers

1. Open the **Providers** page.
2. Add a provider: name, provider type, model, API key, and optionally a custom base
   URL (for OpenAI-compatible endpoints).
3. New providers are active by default. Use **toggle active** to disable one or
   re-enable it — re-enabling tests the connection first and reports a clear error
   (invalid key, model not found, can't connect) if it fails.
4. Only active providers are selectable in the chat page's provider picker.

## Known limitations

- No OCR — scanned PDFs with no extractable text will index with a warning instead
  of useful content.
- Single user, no accounts — anyone with network access to the deployment can use it
  (see Basic Auth in the README for locking it down).
