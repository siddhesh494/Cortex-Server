# Cortex

Cortex is a multi-agent AI assistant. Instead of one big model doing everything, different small jobs are handled by different AI agents — like a team where each person has a clear role.

---

## How to start the project

### 1. Prerequisites

- Python **3.12**
- A running **MongoDB** database (local or Atlas)
- API keys for **Groq** (LLMs), **Tavily** (web search), and **Pinecone** (RAG vectors)

### 2. Create and activate a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

On macOS with Homebrew Python, you may also need:

```bash
export PATH="/opt/homebrew/opt/python@3.12/libexec/bin:$PATH"
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root with:

```env
APP_NAME=Cortex Backend
HOST=127.0.0.1
PORT=8000

MONGO_URI=your_mongodb_connection_string
DATABASE_NAME=chatbot

JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

LOG_LEVEL=INFO

GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key

TITLE_MODEL=openai/gpt-oss-20b
DECISION_MODEL=openai/gpt-oss-20b
SUMMARY_MODEL=llama-3.3-70b-versatile
RESPONSE_MODEL=llama-3.3-70b-versatile

# RAG
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=cortex-rag
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768
RAG_TOP_K=5
EMBEDDING_BATCH_SIZE=8
EMBEDDING_CONCURRENCY=1
GEMINI_API_KEY=your_gemini_api_key
```

On first RAG upload, the server creates the Pinecone index if it does not exist (`dimension=768`, cosine). Embeddings use **gemini-embedding-2** via the **Google Gemini API** (external — no local ONNX). Ingestion embeds and upserts in small batches (`EMBEDDING_BATCH_SIZE`, default 8) with a single in-flight ingestion job.

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Interactive API docs: `http://127.0.0.1:8000/docs`

---

## Architecture

```
User
  │
  ▼
Protected API Gateway          → Login required (JWT). FastAPI entry point.
  │
  ▼
Conversation Manager           → Creates or continues a chat session
  │
  ├── Optional file upload     → Index PDF/TXT into Pinecone + save RAGSummary
  ├── New chat?                → Save session in MongoDB + generate a short title
  └── Existing chat?           → Load past messages, summary, preferences, RAGSummary
  │
  ▼
Decision Agent                 → search | rag_retrieval | no tool
  │
  ├── rag_retrieval            → Similarity search over the session document
  ├── search (Tavily)          → Fetch fresh info from the web
  └── No tool
  │
  ▼
Response Agent                 → Write the final answer using everything above
  │
  ▼
Memory                         → Save the exchange in MongoDB
                                 After ~12 messages, summarize older ones
```

### RAG (document Q&A)

**Indexing** (when a file is attached to `/protected/chat/stream`):

1. Extract text (PDF / TXT)
2. Semantic chunking (LangChain `SemanticChunker`)
3. Embed each batch with gemini-embedding-2 via Gemini
4. Upsert that batch into Pinecone, then release it (filtered by `sessionId` + `userId`)
5. Generate `rag_summary` and store it on the Mongo chat session

**Retrieval** (later messages):

1. Decision agent inspects `rag_summary` vs the user question
2. If relevant → `rag_retrieval` tool embeds the query and searches Pinecone
3. Response agent answers using retrieved chunks

**Rules**

- One document per chat session
- Upload allowed on a new or existing chat
- New-chat titles can use the document excerpt (+ optional user message)
- Stream blocks silently until indexing finishes, then continues the normal chat flow

### `/protected/chat/stream` (multipart)

Send `multipart/form-data` for **every** chat stream request (text-only and with file):

| Field           | Type       | Required                |
|-----------------|------------|-------------------------|
| `message`       | string     | No if `file` is present |
| `chatSessionId` | string     | No (omit = new chat)    |
| `file`          | PDF or TXT | No                      |

Do **not** send `application/json` to this endpoint. Do **not** manually set `Content-Type` when using `FormData` (the browser sets the boundary).

If a second document is uploaded for a session that already has `rag_summary`, the API returns:

```json
{
  "success": false,
  "message": "A document has already been uploaded for this chat session. Only one document is allowed per session.",
  "data": {
    "error": "A document has already been uploaded for this chat session. Only one document is allowed per session."
  }
}
```

### Agents

| Agent           | Role                                      | Model                      |
|-----------------|-------------------------------------------|----------------------------|
| Title Agent     | Names new chats                           | Llama 3.1 8B Instant       |
| Decision Agent  | Chooses search / RAG / no tool            | Llama 3.1 8B Instant       |
| Summary Agent   | Compresses long conversations             | Llama 3.3 70B Versatile    |
| Response Agent  | Writes the final user-facing answer       | Llama 3.3 70B Versatile    |

---

## Project layout (high level)

```
app/
  agents/        # Title, decision, summary, and response agents
  routes/        # Auth + protected chat endpoints
  services/      # Conversation orchestration (ChatService)
  repositories/  # MongoDB access
  tools/         # search + rag_retrieval
  rag/           # Extract → chunk → embed → Pinecone → summary
  memory/        # Chat memory helpers
  models/        # Data shapes for DB
  schemas/       # Request/response validation
```
