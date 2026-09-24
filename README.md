# Compliance & Regulatory Policy AI

A RAG-powered AI assistant that answers compliance and regulatory questions using official regulatory documents — with cited, accurate responses.

**Published frontend:** [https://gentle-field-09e568710.4.azurestaticapps.net/](https://gentle-field-09e568710.4.azurestaticapps.net/)

**Backend recovery is still pending.** See [the deployment scope](PUBLIC-DEPLOYMENT.md) and [Google AI key setup explainer](GOOGLE_AI_SETUP.md) for Free-tier checks, private key configuration and the remaining index/model/backend requirements. A key alone does not guarantee a working AI demo.

---

## Features

- **5 Regulations Supported** — HIPAA, GDPR, FHWA/DOT, NEPA, and ADA
- **RAG Pipeline** — Retrieval-Augmented Generation for grounded, cited answers
- **Multi-turn Chat** — Maintains conversation history for contextual follow-ups
- **Source Citations** — Every answer references specific sections and articles
- **Usage Dashboard** — Track daily requests, token consumption, and model usage
- **Model Tier System** — Automatic fallback across Gemini model tiers based on quota
- **Rate Limiting** — Built-in daily request limits with automatic reset

## Architecture

```
┌─────────────────┐       ┌──────────────────────────────────┐
│  Azure Static   │       │     Google Cloud Run             │
│  Web Apps       │ HTTPS │                                  │
│                 │──────►│  FastAPI Backend                  │
│  index.html     │       │  ├── /ask (POST)                 │
│  app.js         │       │  ├── /regulations (GET)          │
│  dashboard.html │       │  ├── /usage (GET)                │
│  styles.css     │       │  └── /health (GET)               │
└─────────────────┘       │                                  │
                          │  LlamaIndex + ChromaDB           │
                          │  ├── hipaa_docs                  │
                          │  ├── compliance_docs (GDPR)      │
                          │  ├── fhwa_dot_docs               │
                          │  ├── nepa_docs                   │
                          │  └── ada_docs                    │
                          │                                  │
                          │  Gemini API (LLM + Embeddings)   │
                          └──────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript (vanilla) |
| Backend | Python, FastAPI, Uvicorn |
| RAG Framework | LlamaIndex |
| Vector Store | ChromaDB |
| Embeddings | Gemini Embedding 001 |
| LLM | Gemini 2.5 Flash / Flash-Lite / Pro |
| Backend Hosting | Google Cloud Run |
| Frontend Hosting | Azure Static Web Apps |
| CI/CD | GitHub Actions (Azure SWA auto-deploy on push) |

## Regulations Covered

| Regulation | Source | Description |
|-----------|--------|-------------|
| **HIPAA** | 45 CFR Parts 160, 164 | Health Insurance Portability and Accountability Act — privacy, security, breach notification |
| **GDPR** | EU Regulation 2016/679 | General Data Protection Regulation — EU data protection and privacy |
| **FHWA/DOT** | 23 CFR Part 630, Subparts J & K | Federal Highway Administration work zone safety and mobility |
| **NEPA** | 42 USC §§4321–4347, 40 CFR 1500–1508 | National Environmental Policy Act — environmental impact assessments |
| **ADA** | 28 CFR Parts 35 & 36 | Americans with Disabilities Act — accessibility requirements |

## Project Structure

```
compliance-policy-ai/
├── backend/
│   ├── main.py                  # FastAPI application
│   ├── usage_tracker.py         # Request & token tracking
│   ├── Dockerfile               # Cloud Run container
│   ├── requirements.txt         # Python dependencies
│   ├── data/
│   │   ├── hipaa_full_text.txt
│   │   ├── gdpr_full_text.txt
│   │   ├── fhwa_dot_full_text.txt
│   │   ├── nepa_full_text.txt
│   │   └── ada_full_text.txt
│   ├── scripts/
│   │   └── ingest.py            # Document chunking & embedding
│   ├── storage/
│   │   └── chroma_db/           # Vector database
│   └── tests/
│       ├── test_api.py
│       └── test_usage_tracker.py
├── frontend/
│   ├── index.html               # Chat interface
│   ├── app.js                   # Frontend logic
│   ├── styles.css               # UI styles
│   ├── dashboard.html           # Usage dashboard
│   ├── models.html              # Model comparison
│   ├── about.html               # About page
│   └── staticwebapp.config.json # Azure SWA config
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- A Google AI API key ([Get one here](https://aistudio.google.com/apikey))

Start with [Google AI key setup](GOOGLE_AI_SETUP.md) if you need to create or update a key later. Use `GOOGLE_API_KEY` in the backend only; never put it in the frontend or paste it into chat.

### Local Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/krnch/Compliance-AI-test.git
   cd Compliance-AI-test
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

4. **Ingest regulations** (builds the vector database)
   ```bash
   python scripts/ingest.py                    # All regulations
   python scripts/ingest.py --regulation hipaa  # Single regulation
   ```

5. **Start the server**
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```

6. **Open the frontend**
   
   Open `frontend/index.html` in a browser, or serve it with any static file server.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ask` | Ask a question (body: `{question, regulation, chat_history}`) |
| `GET` | `/regulations` | List available regulations |
| `GET` | `/usage` | Get usage statistics |
| `GET` | `/health` | Health check |

### Example Request

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Protected Health Information?", "regulation": "hipaa"}'
```

## Deployment

### Backend (Google Cloud Run)

Follow [the private Cloud Run key-update steps](GOOGLE_AI_SETUP.md#existing-deployed-cloud-run-backend--later-after-ownershipcost-review). Keep credentials out of command history and container images. Key configuration is separate from restoring the backend/index; confirm ownership and separate hosting costs before deployment.

### Frontend (Azure Static Web Apps)

The frontend auto-deploys via GitHub Actions when you push to `main`. Configure via the Azure Portal by connecting your GitHub repo.

## Pages

| Page | URL | Description |
|------|-----|-------------|
| Chat | `/` | Ask compliance questions and get AI-generated answers with source citations |
| Dashboard | `/dashboard.html` | View usage statistics, daily request trends, and token consumption charts |
| Models | `/models.html` | Compare AI model tiers, quota limits, and real-time availability status |
| About | `/about.html` | Architecture overview, tech stack, RAG pipeline explanation |

## License

This project is for educational and demonstration purposes.

---

Built by [Priyanka Chaudhari](https://github.com/chaudharisp)
