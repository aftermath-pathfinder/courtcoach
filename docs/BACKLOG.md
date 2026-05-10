# CourtCoach — Backlog

## Current Milestone: v0.1 (Web App MVP)
Goal: upload a forehand swing video, get 3 coaching observations back.

### In Progress / TODO
- [ ] Bootstrap Vite + React + TypeScript frontend
- [ ] Bootstrap FastAPI backend with health check endpoint
- [ ] Docker + docker-compose setup for backend
- [ ] VideoUploader component (drag-and-drop + file picker)
- [ ] POST /api/analyze endpoint (receives video, returns JSON stub)
- [ ] MediaPipe pose extraction service (real keypoints from video)
- [ ] Joint angle calculation service (elbow, shoulder, hip, knee, follow-through)
- [ ] HuggingFace coaching service (prompt → 3 observations)
- [ ] CoachingCard component (displays feedback)
- [ ] AnalysisStatus component (idle / uploading / processing / done / error states)
- [ ] Wire full flow end-to-end
- [ ] Maestro E2E test: upload video → see coaching card
- [ ] Processing time shown in UI (so user knows 10-20s is expected)
- [ ] Video file size validation (reject >100MB before upload)

### Done
_(nothing yet)_

---

## v0.2 Backlog (do not touch until v0.1 ships)

### Performance
- [ ] Reduce MediaPipe processing time (async frame sampling, optimize params)
- [ ] Video compression in browser before upload (reduces upload size)
- [ ] Progress indicator during server-side processing (websocket or polling)

### Analysis — More Shots
- [ ] Backhand swing analysis
- [ ] Serve analysis
- [ ] Volley analysis

### UI / UX
- [ ] Skeleton overlay on video playback (draw pose keypoints on video)
- [ ] Webcam recording directly in browser (no pre-recorded upload needed)
- [ ] Side-by-side comparison: your swing vs ideal reference angles

### Infrastructure
- [ ] Cloud deployment (Railway or Render) — enables testing on the actual court
- [ ] Environment-based config (dev / prod)

### Data & Tracking
- [ ] Session history (local storage, no auth needed)
- [ ] Progress chart: angle improvements over multiple sessions

### Input Modalities
- [ ] Shot classification + tactical coaching layer
- [ ] Wearable / sensor data integration

### Social
- [ ] Share your analysis (generate a shareable link)
