# PathPilot AI — Backend

FastAPI backend for PathPilot AI. Provides profile analysis, skill-gap detection,
prerequisite-aware roadmap generation, AI coaching (via Gemini), and skill assessment.

## Prerequisites

- **Python 3.10+** (check with `python --version` or `python3 --version`)
- A **Gemini API key** (optional — the app works without it but AI Coach will
  return local-fallback responses instead of LLM-powered answers).
  Get one free at <https://aistudio.google.com/app/apikey>.

## Setup

### 1. Navigate to the backend directory

```bash
cd backend
```

### 2. Create a virtual environment (recommended)

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example and fill in your key:

**Windows:**
```bat
copy .env.example .env
notepad .env
```

**macOS / Linux:**
```bash
cp .env.example .env
nano .env          # or your preferred editor
```

Set these values in `backend/.env`:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash        # optional — defaults to gemini-2.5-flash
```

> `GEMINI_API_KEY` is optional. Without it the backend still starts, but the
> AI Coach returns rule-based fallback answers instead of LLM responses.

## Running

### Start the backend

From the `backend/` directory:

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at **http://127.0.0.1:8000**.

Health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### Start the frontend

Open a **second terminal**, navigate to the `frontend/` directory, and run:

```bash
cd frontend
python -m http.server 5173
```

Then open **http://localhost:5173** in your browser.

## API Endpoints

| Method | Path             | Description                                  |
|--------|------------------|----------------------------------------------|
| GET    | `/api/health`    | Health check; reports if LLM is enabled      |
| POST   | `/api/profile`   | Build/update learner profile → gaps + roadmap|
| POST   | `/api/chat`      | AI Coach conversation                        |
| POST   | `/api/assess`    | Submit skill assessment → regenerate roadmap |
| GET    | `/api/resources` | List curated learning resources              |

## CORS

The backend currently allows all origins (`allow_origins=["*"]`), which is
appropriate for local development. **For any shared or production deployment,
tighten this** to the specific frontend origin (e.g. `http://localhost:5173`).
