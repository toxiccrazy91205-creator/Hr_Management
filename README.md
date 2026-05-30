# HR Agentic AI Recruitment System

An end-to-end AI-powered recruitment pipeline built with **Django**, **LangGraph**, **LangChain**, and **ChromaDB**. The system automates resume screening, interview scheduling, and email drafting — with a strict **Human-in-the-Loop** checkpoint before sending.

---

## 🏗 Architecture

```
┌──────────────┐    ┌───────────────┐    ┌───────────────┐
│  Django Web  │───▶│   LangGraph   │───▶│   ChromaDB    │
│  Frontend    │    │  State Machine│    │  Vector Store │
│  (Templates) │◀───│  (5 Nodes)    │    │  (Local)      │
└──────────────┘    └───────────────┘    └───────────────┘
       │                    │
       │              ┌─────┴─────┐
       │              │  LLM API  │
       │              │ (OpenRouter│
       │              │ / NVIDIA)  │
       │              └───────────┘
       ▼
┌──────────────┐
│  Human-in-   │
│  the-Loop    │
│  Approval    │
└──────────────┘
```

## 🤖 AI Pipeline (LangGraph Workflow)

1. **Ingest Resumes** → Parse PDF/DOCX, chunk text, store in ChromaDB
2. **Screen Candidates** → RAG retrieval + LLM scoring against job requirements
3. **Schedule Interviews** → AI assigns time slots to shortlisted candidates
4. **Draft Emails** → AI writes personalized interview invitation emails
5. **⏸ PAUSE — Human Review** → HR reviews shortlist + email drafts
6. **Send Emails** → Upon approval, dispatches via Django `send_mail`

## 🚀 Quick Start

### 1. Clone & Configure

```bash
cd hr_agent_project
cp .env.example .env
# Edit .env with your API key
```

### 2. Run with Docker

```bash
docker-compose up --build
```

### 3. Run Locally (without Docker)

```bash
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 4. Open in Browser

Navigate to **http://localhost:8000**

## 📁 Project Structure

```
hr_agent_project/
├── manage.py
├── requirements.txt
├── Dockerfile & docker-compose.yml
├── .env.example
├── hr_agent_project/          # Django settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py & asgi.py
├── core/                       # Django app
│   ├── models.py              # JobPosting, Candidate
│   ├── views.py               # Dashboard, Approval, Success
│   ├── urls.py
│   ├── admin.py
│   └── templates/
│       ├── base.html          # Design system
│       ├── dashboard.html     # Upload + job form
│       ├── approval.html      # HITL review page
│       └── success.html       # Confirmation
└── ai_engine/                  # AI orchestration
    ├── vector_store.py        # ChromaDB ingestion & retrieval
    ├── agents.py              # LLM + prompt templates
    └── graph.py               # LangGraph state machine
```

## ⚙️ Configuration

All config is via environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | API key for LLM | *(required)* |
| `OPENROUTER_BASE_URL` | LLM API base URL | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | Model name | `openai/gpt-3.5-turbo` |
| `EMAIL_BACKEND` | Django email backend | Console (prints to terminal) |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./chroma_db` |

## 📧 Email Configuration

By default, emails are printed to the console (no actual sending). To use real SMTP:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 📄 License

MIT
