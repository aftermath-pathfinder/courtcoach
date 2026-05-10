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
  video: File   (MP4 or MOV, max 100MB, max 30 seconds)
```

**Response 200**
```json
{
  "status": "success",
  "processing_time_seconds": 14.3,
  "keypoints_extracted": 42,
  "angles": {
    "elbow_angle": 162.4,
    "shoulder_rotation": 87.1,
    "knee_flex": 28.6,
    "hip_turn": 76.3,
    "follow_through": 195.2
  },
  "coaching_feedback": [
    "Your elbow angle at contact is excellent — nearly straight arm generates maximum power.",
    "Your shoulder rotation is within the ideal range, but try to initiate the turn earlier from the split step.",
    "Increase your knee flex slightly to 30-35° for a more powerful ground-up kinetic chain."
  ]
}
```

**Response 422 — Invalid input**
```json
{
  "status": "error",
  "message": "Video file too large. Maximum size is 100MB."
}
```

**Response 500 — Processing failure**
```json
{
  "status": "error",
  "message": "Pose estimation failed — ensure the full body is visible in the video."
}
```

---

## Frontend API Client Contract

The frontend `api/client.ts` must export:

```typescript
export async function analyzeSwing(file: File): Promise<AnalysisResult>
// Throws an Error with a user-readable message on failure
```

All other fetch logic stays in `client.ts` — components only call this function.
