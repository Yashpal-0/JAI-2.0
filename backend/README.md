# 🐍 Zerostic JAI 2.0 — Backend Agent Engine

The backend of JAI 2.0 is a state-of-the-art Python-based agent engine built using **FastAPI** and **LangGraph**. It powers the stateful conversation graphs, enforces operational alignment guidelines (e.g., never quoting prices, staying on-topic), runs localized Retrieval-Augmented Generation (RAG) against Zerostic documentation, and streams real-time token-level Server-Sent Events (SSE) to the frontend client.

---

## 🌟 Core Features

- 🧠 **LangGraph Orchestrator**: Uses state graphs to model agent workflows. It houses system prompts, guards, classifier layers, and tool-calling states.
- 📦 **Dual-Layer Database System**:
  - `checkpoints.db` (SQLite): Persists complex multi-turn LangGraph agent history states.
  - `chat_history.db` (SQLite): Tracks general conversation sessions, updates, titles, and ownership for instant loading in the UI sidebar.
- 🔍 **Automated RAG Pipeline**: Uses **ChromaDB** and local embeddings to index documents stored in the `docs/` folder on startup.
- 🚀 **Server-Sent Events (SSE)**: Streams text chunks to the client in real time via FastAPI's `StreamingResponse`, filtering out internal classifier tokens for a pristine user experience.
- 🎛️ **Offline Interactive Console**: Includes a command-line terminal (`main.py`) for offline testing, debugging, and direct interaction with the agent graph.

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python >= 3.11** installed on your system.
- `venv` or `virtualenv` for environment isolation.

### 1. Environment Configuration
Navigate into the `backend/` directory, create a Python virtual environment, and activate it:
```bash
cd backend
python -m venv .venv

# On Linux / macOS
source .venv/bin/activate

# On Windows (Command Prompt)
.venv\Scripts\activate.bat

# On Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
Install the required packages using pip:
```bash
pip install -r requirements.txt
```
*(Alternatively, if you have `uv` installed, run `uv pip install -r requirements.txt` for extremely fast installations)*

### 3. Environment Variables
Copy the template environment file to create your own:
```bash
cp .env.example .env
```
Open the `.env` file and configure the settings. Below is a summary of active configurations:

| Variable | Required | Default / Example Value | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | **Yes** | `sk-or-v1-...` | API Key used to connect to OpenRouter's gateway. |
| `OPENROUTER_MODEL` | No | `meta-llama/llama-3.3-70b-instruct:free` | The primary LLM to route agent reasoning tasks to. |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Comma-separated list of origins allowed to call the endpoints. |
| `LANGSMITH_TRACING` | No | `true` | Enables active tracing outputs to LangSmith. |
| `LANGSMITH_API_KEY` | No | `lsv2_pt_...` | API Key for LangSmith dashboard monitoring. |
| `LANGSMITH_PROJECT` | No | `"JAI-2.0"` | Project tracking namespace in LangSmith. |

---

## 💾 Relational Storage & RAG Pipelines

### Relational Database Init
On startup, FastAPI calls `init_db()` (defined in `db.py`) which initializes a lightweight SQLite database `chat_history.db` containing a `threads` table. This tracks thread IDs, associated User IDs, Tenant IDs, custom created-at timestamps, and the generated titles.

### RAG Auto-Ingestion
The FastAPI lifespan loader automatically checks for documentation changes.
1. It reads all files placed inside the `backend/docs/` folder (markdown, text, etc.).
2. It breaks the files down into semantic chunks using LangChain text splitters.
3. Chunks are embedded and stored inside the local `backend/chroma_db/` vector storage.
4. When a user asks JAI a question, JAI performs a semantic lookup against this vector database to answer accurately based on real Zerostic guidelines and products.

---

## 🏃 Running the Application

You can interact with the backend in two ways:

### 🌐 Option A: Launch the FastAPI Web Server (For Frontend UI)
Run the web application server via Uvicorn:
```bash
python -m uvicorn api:app --reload --port 8000
```
This runs the REST and streaming API at **`http://localhost:8000`**. The `--reload` flag detects local file changes and restarts the server automatically.

### 💻 Option B: Run the Offline Terminal Chat (For CLI testing)
To test agent performance or run developer benchmarks without launching a web server:
```bash
python main.py
```
This starts an interactive, stateful terminal prompt. Type your messages, and see JAI's answers printed directly to the shell. Type `exit` or `quit` to stop.

---

## 🔌 API Endpoint Reference

| Method | Endpoint | Query / Body Details | Description |
|---|---|---|---|
| **GET** | `/health` | None | System status and connectivity check. |
| **GET** | `/threads` | `?user_id=...&tenant_id=...` | Retrieves a list of active threads associated with the user/tenant. |
| **DELETE** | `/threads/{id}`| `?user_id=...` | Removes a chat thread from SQLite and purges LangGraph checkpoints. |
| **GET** | `/threads/{id}/messages` | `?user_id=...` | Fetches historical messages from the LangGraph checkpointer for the thread. |
| **POST** | `/chat` | **Body (JSON)**: `ChatRequest` | Streams real-time AI responses as text/event-stream (SSE). |

### Chat Request Schema (`POST /chat`)
```json
{
  "message": "Hi, tell me about AppLab",
  "user_id": "ui_user",
  "tenant_id": "zerostic.com",
  "thread_id": "8f8b8a8b-1234-abcd-ef01-123456789abc",
  "title": "Optional Custom Title"
}
```
The response returns a Server-Sent Event stream. It emits data chunks matching the ongoing assistant thoughts, concluding with `data: [DONE]`.
