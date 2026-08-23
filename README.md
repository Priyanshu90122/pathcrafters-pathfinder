# PathFinder

A Gemini-powered learning assistant that turns a learner's natural-language goal, experience, skills, time budget and feedback into an adaptive roadmap of resources, projects, prerequisites and milestones.

## What is dynamic
- Natural-language learner profile → role/experience/time inference
- Skill-gap analysis against role targets
- Prerequisite-aware roadmap generation
- Gemini AI Coach with structured plan updates
- AI Coach changes are reflected back into the dashboard roadmap
- Skill assessment updates learner state and regenerates the roadmap
- Resources and portfolio projects are tied to skills

## Run on Windows
```bat
cd backend
python -m pip install -r requirements.txt
notepad .env
```
Put this in `backend/.env`:
```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```
`GEMINI_MODEL` is optional; if supplied, it is used. Otherwise the default in the backend is used.

Start backend:
```bat
python -m uvicorn app.main:app --reload
```

In a second terminal:
```bat
cd frontend
python -m http.server 5173
```
Open http://localhost:5173

Health check: http://127.0.0.1:8000/api/health

## Demo test
1. Create a profile: "I want to become an AI Engineer, have 6 hours/week, know Python, and I am weak in deep learning."
2. Ask AI Coach: "I only have 8 weeks. Prioritize deployment and MLOps and deprioritize NLP."
3. Confirm the dashboard roadmap changes immediately.
4. Run Skill Assessment and change a skill score; the roadmap regenerates.

