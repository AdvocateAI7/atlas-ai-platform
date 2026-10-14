# Conversation Sessions

The `/sessions` feature enables stateful, multi-turn conversations with the LLM. Each session stores its full message history in the database. When a new message is sent, the last 10 turns of that session are automatically included in the prompt so the model has context.

---

## Endpoints

### Create a session
```
POST /sessions
Content-Type: application/json

{"title": "Support chat 2024-10-14"}
```
**Response 201**
```json
{
  "id": 1,
  "title": "Support chat 2024-10-14",
  "created_at": "2024-10-14T10:00:00",
  "updated_at": "2024-10-14T10:00:00",
  "message_count": 0
}
```

### List all sessions
```
GET /sessions
```

### Get a session with full history
```
GET /sessions/{session_id}
```

### Send a message
```
POST /sessions/{session_id}/messages
Content-Type: application/json

{"message": "What did we discuss earlier?", "temperature": 0.3}
```
**Response 201**
```json
{
  "id": 4,
  "role": "assistant",
  "content": "...",
  "provider": "mock",
  "created_at": "2024-10-14T10:01:00"
}
```

### Delete a session
```
DELETE /sessions/{session_id}
```
Returns `204 No Content`. All messages are deleted with the session.

---

## How context works

Each `POST /sessions/{id}/messages` call:
1. Persists the user message to the database
2. Loads the last 10 messages from that session
3. Formats them as a conversation transcript and prepends it to the prompt
4. Calls the configured LLM provider
5. Persists and returns the assistant reply

The history window (10 turns) prevents very long sessions from exceeding model context limits while keeping recent context available.

---

## Database schema

| Table | Columns |
|---|---|
| `conversation_sessions` | `id`, `title`, `created_at`, `updated_at` |
| `conversation_messages` | `id`, `session_id` (FK), `role`, `content`, `provider`, `created_at` |

Sessions cascade-delete their messages on removal.
