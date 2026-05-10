# CourtCoach

Upload a tennis forehand swing video. Get AI-powered coaching feedback on your form.

## Stack
- **Frontend:** React 18 + Vite + TypeScript + Tailwind
- **Backend:** FastAPI + Python 3.11 + MediaPipe + HuggingFace
- **Container:** Docker (backend only)
- **Testing:** Vitest (frontend), pytest (backend), Maestro (E2E)

---

## Prerequisites
- Node.js 20+
- Python 3.11+
- Docker Desktop (running)
- Maestro CLI (`brew install maestro` on macOS)

---

## Setup

### 1. Clone and configure environment
```bash
cp .env.example .env
# Edit .env — add your HuggingFace token
```

### 2. Start the backend (Docker)
```bash
docker-compose up --build
# Backend running at http://localhost:8000
# Visit http://localhost:8000/health to confirm
```

### 3. Start the frontend
```bash
cd frontend
npm install
npm run dev
# Frontend running at http://localhost:5173
```

### 4. Use the app
- Open http://localhost:5173
- Upload a 5–10 second forehand swing video (MP4 or MOV, max 100MB)
- Wait ~15 seconds for analysis
- Read your coaching feedback

---

## Filming Tips (for best results)
- Film from the side — camera perpendicular to your swing path
- Position camera at hip height, ~5 meters away
- Ensure full body is visible: head to feet
- Good lighting — avoid backlight (don't film toward the sun)
- Capture one clean swing — 5–10 seconds

---

## Development

See `CLAUDE.md` for full development guide.

```bash
# Run all tests
/test all   # Claude Code command

# Run backend tests only
cd backend && pytest -v

# Run frontend tests only
cd frontend && npm run test

# Run E2E
maestro test .maestro/flows/
```

---

## Project Structure
```
courtcoach/
├── frontend/                    # React + Vite app
│   └── src/
│       ├── api/client.ts        # all backend calls
│       ├── components/          # UI components + tests
│       ├── pages/               # page views
│       └── types/analysis.ts    # shared TypeScript types
├── backend/                     # FastAPI app
│   └── app/
│       ├── main.py              # app entry point
│       ├── routes/              # API endpoints
│       └── services/            # pose, angle, coaching logic
│           ├── pose_service.py
│           ├── angle_service.py
│           └── coaching_service.py
├── docs/
│   ├── API.md                   # endpoint contracts
│   ├── ML_ARCHITECTURE.md       # ML pipeline docs
│   └── BACKLOG.md               # feature backlog
├── .maestro/flows/              # E2E test flows
├── .claude/                     # Claude Code agents + commands
├── docker-compose.yml
├── CLAUDE.md                    # Claude Code context
└── .env.example
```
