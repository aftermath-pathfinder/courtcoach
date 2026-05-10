# CourtCoach — Backlog

## Current Milestone: v0.3 (Conversational Coach)
Goal: multi-turn AI coaching chat grounded in the player's own biomechanical data.

### Done
- [x] `POST /api/chat` endpoint — OpenAI `gpt-4o-mini`, multi-turn messages + analysis context
- [x] System prompt auto-built from angles, severities, coaching tips, and key frame data
- [x] `ChatSidebar` component — message bubbles, Enter to send, animated loading dots, error state
- [x] Chat context derived from analysis result and passed automatically after every upload

### TODO
- [ ] LLM provider abstraction — swap between OpenAI / Claude / HuggingFace via `LLM_PROVIDER` env var
- [ ] Vision mode — send annotated key frame images to GPT-4o or Claude so the coach literally *sees* the pose
- [ ] Self-assessment onboarding form (NTRP-style, stored in localStorage, injected as soft context)
- [ ] Skill level assessment (5-tier NTRP from biomechanics + self-assessment, surfaces perception gaps)
- [ ] Maestro E2E test: upload video → chat with coach

---

## v0.2 — Done
Goal: key-frame detection, skeleton overlays, structured coaching tips with drills, severity computed locally.

- [x] Key-frame detection: contact point, wind-up, follow-through frames from per-frame angle analysis
- [x] Color-coded skeleton overlay drawn on each key frame (green/orange/red by angle severity)
- [x] Structured coaching tips: `{angle_name, severity, observation, drill}` — severity from IDEAL_RANGES, never delegated to LLM
- [x] `constants.py`: shared IDEAL_RANGES and BOUNDARY_TOLERANCE
- [x] `extract_keypoints_per_frame()`: per-frame keypoints with frame indices
- [x] Breaking API change: `coaching_feedback` → `tips` + `key_frames`; `key_frames` include per-frame `angles` dict
- [x] Frontend: KeyFramePanel — vertical stack (full-width images), per-phase angle rows with human descriptions
- [x] Frontend: CoachingCard updated with severity badge + drill section
- [x] Key frame images: resized to 800px max width, JPEG quality 85% (up from 50%) for sharpness

---

## v0.1 — Done
- [x] Bootstrap Vite + React + TypeScript frontend
- [x] Bootstrap FastAPI backend with health check endpoint
- [x] Docker + docker-compose setup (frontend + backend fully containerised)
- [x] VideoUploader component (drag-and-drop + file picker, 100 MB client-side validation)
- [x] POST /api/analyze endpoint (size check, error handling, real pipeline response)
- [x] MediaPipe pose extraction service (BlazePose FULL, middle 60% frames, visibility filter)
- [x] Joint angle calculation service (elbow, shoulder, hip, knee, follow-through)
- [x] HuggingFace coaching service (Gemma-2-2b-it, JSON parse, 3-item fallback)
- [x] CoachingCard component
- [x] AnalysisStatus component (idle / uploading / processing / done / error + processing time)
- [x] Wire full pipeline end-to-end (pose → angles → coaching → JSON response)
- [x] Processing time shown in UI
- [x] Video file size validation (client-side + server-side)
- [x] Unit tests: 36 backend + frontend component tests all passing

---

## v0.3 — Conversational Coach

### Chat Sidebar
- [ ] Chat endpoint: `POST /api/chat` — accepts `{messages, analysis_id?}`
- [ ] Analysis context injected as system prompt: angles, severities, key frame descriptions
- [ ] Multi-turn conversation history stored in frontend state (no DB needed yet)
- [ ] "No video" mode: coach references last analysis or responds to self-assessment context only
- [ ] **LLM provider abstraction**: swappable between Claude, OpenAI, HuggingFace via `LLM_PROVIDER` env var
  - Claude (Anthropic SDK) — recommended for chat quality
  - OpenAI (GPT-4o) — fallback, user has tokens
  - HuggingFace (current) — cheap, lower quality for chat
- [ ] **Vision mode**: if provider supports it (Claude 3.5+, GPT-4o), send annotated key frame images to LLM — coach literally *sees* the pose, not just reads angles
- [ ] UI: sidebar or bottom panel that opens after analysis completes

### Self-Assessment Onboarding Form
- [ ] Shown to new users before first video upload (skippable)
- [ ] NTRP-style questions:
  - How long have you been playing tennis?
  - Can you sustain 10+ shot rallies?
  - Do you compete in leagues or tournaments?
  - Do you hit with topspin, slice, or mostly flat?
  - Do you feel you generate enough topspin, or does your ball tend to float?
  - Does your arm feel tired after long rallies or do you get shoulder/elbow pain?
  - Do you hit better when you have time to set up vs. on the run?
  - Anything you'd like to share about your tennis or practice environment?
- [ ] Stored in localStorage as soft prior — never treated as ground truth
- [ ] Injected as context into chat system prompt with explicit caveat: "video data overrides self-assessment"

### Skill Level Assessment
- [ ] NTRP-based 5-tier system: Beginner (1.5–2.0) / Novice (2.5–3.0) / Intermediate (3.0–3.5) / Club (3.5–4.5) / Advanced (4.5+)
- [ ] Coach assigns level from three signals (priority order):
  1. Video biomechanics: consistency score (angle variance across frames), technique score (deviation from IDEAL_RANGES), kinetic chain sequencing (hip precedes shoulder)
  2. Self-assessment form answers
  3. Perception gap: if self-rated level conflicts with biomechanical evidence, surface the gap explicitly — *"You described yourself as a 4.0 player but your elbow variance is 22° — that's an Intermediate consistency signature"*
- [ ] Level affects coaching tone: beginners get 1 fix at a time + simple drill language; advanced get kinetic chain detail + tactical cues
- [ ] Level displayed in UI and updated after each session

---

## v0.4 — Broader Shot Coverage

### Shot Type Selection
- [ ] Manual shot type selector: Forehand / Backhand (1H) / Backhand (2H) / Serve / Volley
- [ ] Shot-type-specific IDEAL_RANGES (serve contact ≠ forehand contact ideals)
- [ ] Coaching prompt updated to reflect selected shot type
- [ ] Rule-based auto-detection (fallback to manual): serve = dominant wrist rises above shoulder, backhand = wrist crosses body midline

### Fix follow_through Metric
- [ ] Currently computed as `elbow_angle + 30°` — this is a placeholder and must be replaced
- [ ] Real follow-through: track wrist arc across per-frame keypoints, compute max angle of swing arc
- [ ] Already enabled by `extract_keypoints_per_frame()` — just needs the arc calculation

### Shot-to-Shot Consistency Scoring
- [ ] Upload 3 clips of the same shot → get variance score per angle
- [ ] High variance = inconsistent technique, often more actionable than any single-swing analysis
- [ ] Displayed as a consistency radar/bar chart

---

## v0.5 — Intelligence & Personalization

### Player Style Library
- [ ] Reference pose library for specific shot styles:
  - *"Learn Nadal's forehand"* — extreme western grip, heavy topspin, shoulder/hip ratio signatures
  - *"Learn Federer's 1H backhand"* — one-handed extension, shoulder drop timing
  - *"Learn Rybakina's serve"* — flat, high toss, coil depth
  - *"Learn Djokovic's baseline forehand"* — neutral grip, extreme consistency
- [ ] Reference skeleton overlay alongside user's pose on key frames
- [ ] Angle delta display: *"Your elbow: 147° vs Nadal: 168° (−21°)"*
- [ ] Requires curated reference keypoint dataset per player/shot (manual curation or scraping from broadcast footage)

### Auto Action Classification (ML)
- [ ] Fine-tune lightweight classifier (LSTM or small Transformer) on MediaPipe keypoint sequences
- [ ] Training data: [tennis player actions dataset (COCO format)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11282921/) — forehand, backhand, ready position, serve
- [ ] Replaces manual shot type selector for known shot types
- [ ] Research baseline: ST-GCN-CAD and CNN-BiLSTM achieve high accuracy on 5-class tennis movement recognition

---

## v0.6 — Progress & Plans

### Session History
- [ ] localStorage-based session history (no auth, no DB)
- [ ] View past analyses with angles + tips
- [ ] Angle trend chart: improvement over multiple sessions per angle

### Weekly Drill Plans
- [ ] Generated by LLM based on: current level, weakest angles, selected shot type, frequency of play
- [ ] Structured as: 3–5 drills per week, each with reps/sets and focus cue
- [ ] Adapted each week if user uploads new video (progress-aware)

---

## Infrastructure / Evergreen
- [ ] Cloud deployment (Railway or Render) — enables testing on actual court
- [ ] Environment-based config (dev / prod)
- [ ] CVE scanning: `npm audit` + `pip-audit` in CI
- [ ] Session history (localStorage, no auth needed)
- [ ] Share your analysis (generate a shareable link)
- [ ] Maestro E2E tests for new flows (chat, key frames, onboarding form)



Notes: Use roger federer videos haha. Its being called out without the context of the ball being received and the hitting strategy
