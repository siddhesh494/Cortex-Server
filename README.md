# Cortex

Cortex is a multi-agent AI assistant. Instead of one big model doing everything, different small jobs are handled by different AI agents — like a team where each person has a clear role.

---

## How to start the project

### 1. Prerequisites

- Python **3.12**
- A running **MongoDB** database (local or Atlas)
- API keys for **Groq** (LLMs) and **Tavily** (web search)

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

TITLE_MODEL=llama-3.1-8b-instant
DECISION_MODEL=llama-3.1-8b-instant
SUMMARY_MODEL=llama-3.3-70b-versatile
RESPONSE_MODEL=llama-3.3-70b-versatile
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

You can check it’s running by opening `/` — you should see a success message.

Interactive API docs: `http://127.0.0.1:8000/docs`

---

## Architecture

Think of Cortex like a smart receptionist who remembers past chats, decides when to look things up online, and then writes a clear reply.

```
User
  │
  ▼
Protected API Gateway          → Login required (JWT). FastAPI entry point.
  │
  ▼
Conversation Manager           → Creates or continues a chat session
  │
  ├── New chat?                → Save session in MongoDB + generate a short title
  └── Existing chat?           → Load past messages, summary, key points, and preferences
  │
  ▼
Decision Agent                 → “Do we need the internet for this?”
  │
  ├── Yes → Tavily Search      → Fetch fresh info from the web
  └── No  → Skip search
  │
  ▼
Response Agent                 → Write the final answer using everything above
  │
  ▼
Memory                         → Save the exchange in MongoDB
                                 After ~12 messages, summarize older ones so context stays short
```

### Step by step (simple version)

**1. Protected API Gateway**  
Every chat request goes through an authenticated API. Only logged-in users can talk to Cortex.

**2. Conversation management**  
- **New conversation:** create a MongoDB session and ask a small model to invent a short chat title.  
- **Existing conversation:** load recent messages, a running summary, key points, and how the user likes answers formatted.

**3. Decision agent**  
A lightweight model decides if an external tool is needed. Today that tool is **Tavily Search** — used when the user asks for something that needs up-to-date info (news, current events, etc.).

**4. Response generation**  
The response agent builds the final answer from:
- the user’s question  
- chat history + summary + key points  
- response preferences  
- search results (if any)

**5. Memory management**  
Each turn is stored in MongoDB. When a conversation grows past about **12 messages**, an LLM writes a short summary of older messages. That keeps later replies smart without sending the entire chat every time — and it can remember things like preferred tone or format.

### Why multiple agents?

One model can do everything, but it’s often slower, more expensive, or worse at specialized jobs. Cortex splits work:

| Agent           | Role                                      | Model                      |
|-----------------|-------------------------------------------|----------------------------|
| Title Agent     | Names new chats                           | Llama 3.1 8B Instant       |
| Decision Agent  | Chooses whether to search the web         | Llama 3.1 8B Instant       |
| Summary Agent   | Compresses long conversations             | Llama 3.3 70B Versatile    |
| Response Agent  | Writes the final user-facing answer       | Llama 3.3 70B Versatile    |

Smaller / faster models handle quick decisions and titles. A stronger model handles summarizing and answering, where quality matters more.

### What this stack teaches

Building an AI app is more than writing a good prompt. You also need:

- **Memory** — what to store and when to compress it  
- **Context** — what to send the model so answers stay relevant  
- **Orchestration** — which agent runs when  
- **Model choice** — matching size/cost to each job  

---

## Project layout (high level)

```
app/
  agents/        # Title, decision, summary, and response agents
  routes/        # Auth + protected chat endpoints
  services/      # Conversation orchestration (ChatService)
  repositories/  # MongoDB access
  tools/         # External tools (e.g. Tavily search)
  memory/        # Chat memory helpers
  models/        # Data shapes for DB
  schemas/       # Request/response validation
```
