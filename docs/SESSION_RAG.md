# Session-Aware RAG Pipeline

Documents can be uploaded to a specific conversation session. When a message is sent, the platform automatically retrieves the most relevant chunks from that session's documents and passes them as context to the LLM alongside the conversation history.

---

## Endpoints

### Upload a document to a session
```
POST /sessions/{session_id}/documents
Content-Type: application/json

{"text": "...", "filename": "reference.txt"}
```
**Response 201**
```json
{
  "id": 1,
  "filename": "reference.txt",
  "chunk_count": 3,
  "session_id": 5,
  "created_at": "2024-10-14T10:00:00"
}
```

### List session documents
```
GET /sessions/{session_id}/documents
```

### Delete a session document
```
DELETE /sessions/{session_id}/documents/{document_id}
```
Returns `204 No Content`. All chunks are deleted with the document.

### Send a message (with optional RAG)
```
POST /sessions/{session_id}/messages
Content-Type: application/json

{"message": "What does the doc say about rate limiting?", "use_rag": true}
```
**Response 201** — includes a `sources` field listing document IDs used:
```json
{
  "id": 12,
  "role": "assistant",
  "content": "...",
  "provider": "mock",
  "sources": [1],
  "created_at": "2024-10-14T10:01:00"
}
```

Set `"use_rag": false` to skip document retrieval entirely.

---

## How it works

1. Documents uploaded to a session are chunked and embedded using the existing pipeline.
2. On each `POST /sessions/{id}/messages`, if `use_rag` is true, the top-K chunks from that session's documents are retrieved via cosine similarity.
3. Retrieved context (capped at 4,000 characters) is prepended to the prompt alongside conversation history.
4. The response includes `sources`: the list of document IDs whose chunks were used.

---

## Session isolation

Documents belong to exactly one session. Retrieval only searches within the requesting session — documents from other sessions are never visible. Deleting a session removes its documents and chunks.

---

## Database schema additions

| Table | New columns |
|---|---|
| `documents` | `session_id` (FK → conversation_sessions, nullable), `filename` |

A null `session_id` indicates a legacy global document ingested via `/documents`.
