# CourtCoach — API Reference

Base URL (local dev): `http://localhost:8000`

---

## GET /health
Health check. Returns 200 if backend is running.

**Response**
```json
{ "status": "ok" }
```

---

## POST /api/analyze
Upload a tennis swing video and receive pose analysis + coaching feedback.

**Request**
```
Content-Type: multipart/form-data
Body:
  video: File   (MP4 or MOV, max 100 MB)
```

**Response 200**
```json
{
  "status": "success",
  "processing_time_seconds": 14.3,
  "keypoints_extracted": 10,
  "angles": {
    "elbow_angle": 147.0,
    "shoulder_rotation": 88.0,
    "hip_turn": 80.0,
    "knee_flex": 28.0,
    "follow_through": 177.0
  },
  "tips": [
    {
      "angle_name": "elbow_angle",
      "severity": "critical",
      "observation": "Your elbow angle at contact is 147° — too bent. Aim for 160–170°.",
      "drill": "Shadow swing drill: practice slow-motion swings extending your arm fully at contact."
    }
  ],
  "key_frames": [
    {
      "label": "contact",
      "angles": {
        "elbow_angle": 147.0,
        "shoulder_rotation": 88.0,
        "hip_turn": 80.0,
        "knee_flex": 28.0,
        "follow_through": 177.0
      },
      "image_b64": "<base64-encoded JPEG>",
      "annotated_image_b64": "<base64-encoded JPEG with skeleton overlay>"
    }
  ]
}
```

**Field notes**
- `keypoints_extracted` — always **10** on success (both shoulders, elbows, wrists, hips, knees)
- `tips` — 1–5 structured coaching observations; `severity` is one of `"good"`, `"warning"`, `"critical"`, computed locally from `IDEAL_RANGES` (never delegated to the LLM)
- `key_frames` — 1–3 items: `"contact"`, `"windup"`, `"follow_through"`. Images are 800px-wide JPEG at 85% quality, base64-encoded. `angles` are the per-frame values for that specific swing moment.

**Response 422 — Invalid input or pose extraction failure**
```json
{
  "detail": {
    "status": "error",
    "message": "Video file too large. Maximum size is 100MB."
  }
}
```

---

## POST /api/analyze/stream
Same pipeline as `/api/analyze` but streams progress as Server-Sent Events.

**Request** — identical to `/api/analyze`.

**Response** — `Content-Type: text/event-stream`. Each event is a `data: {json}\n\n` line.

**Event stages (in order)**

| `stage`      | When emitted                              |
|---|---|
| `extracting` | MediaPipe pose extraction starting        |
| `angles`     | Extraction done, computing joint angles   |
| `coaching`   | Angles done, calling LLM for tips         |
| `keyframes`  | Tips done, selecting and annotating frames|
| `done`       | All done — `data` field contains full result (same shape as `/api/analyze` 200 response) |
| `error`      | Any failure — `message` field has reason  |

**Example events**
```
data: {"stage": "extracting", "message": "Extracting pose keypoints with BlazePose…"}

data: {"stage": "angles", "message": "Detected 8 valid frames. Computing joint angles…"}

data: {"stage": "coaching", "message": "Computing angles done. Generating structured coaching tips…"}

data: {"stage": "keyframes", "message": "Identifying key swing moments and drawing overlays…"}

data: {"stage": "done", "message": "Analysis complete in 14.3s.", "data": { ...full result... }}
```

---

## POST /api/chat
Multi-turn coaching conversation grounded in a prior analysis.

**Request**
```json
{
  "messages": [
    { "role": "user", "content": "Why is my elbow angle bad?" },
    { "role": "assistant", "content": "Your elbow at contact is 147°…" },
    { "role": "user", "content": "What drill should I do?" }
  ],
  "analysis_context": {
    "angles": { "elbow_angle": 147.0, "shoulder_rotation": 88.0, "hip_turn": 80.0, "knee_flex": 28.0, "follow_through": 177.0 },
    "tips": [ { "angle_name": "elbow_angle", "severity": "critical", "observation": "...", "drill": "..." } ],
    "key_frames": [ { "label": "contact", "angles": { ... } } ]
  }
}
```

- `messages` — full conversation history, newest last. Send every prior turn so the model has context.
- `analysis_context` — optional. When provided, the system prompt includes angle values, severities, drills already given, and key frame data. Omit if no analysis has been run yet.

**Response 200**
```json
{ "reply": "To improve your elbow extension, try the shadow swing drill…" }
```

**Response 500 — Missing API key**
```json
{
  "detail": {
    "status": "error",
    "message": "OPENAI_API_KEY environment variable is not set."
  }
}
```

---

## Frontend API Client Contract

`frontend/src/api/client.ts` exports:

```typescript
// Non-streaming analysis
analyzeSwing(file: File): Promise<AnalysisResult>

// Streaming analysis with progress callbacks
analyzeSwingStream(file: File, onProgress: (message: string) => void): Promise<AnalysisResult>

// Multi-turn coaching chat
sendChatMessage(messages: ChatMessage[], context: ChatContext | null): Promise<string>
```

All fetch logic stays in `client.ts` — components only call these functions.
