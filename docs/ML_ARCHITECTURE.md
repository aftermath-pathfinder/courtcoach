# CourtCoach — ML Architecture

## Pipeline Overview

```
Video File (MP4/MOV)
        ↓
[OpenCV] Extract frames
        ↓
[MediaPipe BlazePose] Detect 33 body keypoints per frame
        ↓
[Angle Service] Compute 5 joint angles from averaged keypoints
        ↓
[HuggingFace Inference API] Generate 3 coaching observations
        ↓
JSON response to frontend
```

---

## Stage 1: Frame Extraction (OpenCV)

- Library: `opencv-python`
- Input: video file as bytes (never written to disk)
- Extract all frames, skip first and last 20% (often blurry or mid-motion)
- Target: process middle 60% of frames for keypoint averaging

---

## Stage 2: Pose Estimation (MediaPipe BlazePose)

- Library: `mediapipe`
- Model: BlazePose FULL (higher accuracy than LITE, acceptable for non-real-time)
- Output: 33 landmarks, each with (x, y, z, visibility)
- Key landmarks used:
  | Index | Name |
  |---|---|
  | 11 | LEFT_SHOULDER |
  | 12 | RIGHT_SHOULDER |
  | 13 | LEFT_ELBOW |
  | 14 | RIGHT_ELBOW |
  | 15 | LEFT_WRIST |
  | 16 | RIGHT_WRIST |
  | 23 | LEFT_HIP |
  | 24 | RIGHT_HIP |
  | 25 | LEFT_KNEE |
  | 26 | RIGHT_KNEE |

- Averaging strategy: collect landmarks across all valid frames, compute mean x/y per landmark
- Validity check: only use frames where `visibility > 0.5` for all required landmarks

---

## Stage 3: Angle Calculation

Five angles computed for forehand analysis:

| Angle | Landmarks Used | Formula |
|---|---|---|
| Elbow angle | SHOULDER → ELBOW → WRIST | 3-point angle at ELBOW |
| Shoulder rotation | LEFT_SHOULDER ↔ RIGHT_SHOULDER vs hip plane | rotation delta |
| Hip turn | LEFT_HIP ↔ RIGHT_HIP vs shoulder plane | rotation delta |
| Knee flex | HIP → KNEE → ANKLE (approx) | 3-point angle at KNEE |
| Follow-through | SHOULDER → ELBOW → WRIST at peak | highest wrist Y position frame |

Reference ranges (ideal forehand):
- Elbow: 160–170° at contact
- Shoulder rotation: 80–100°
- Hip turn: 70–90°
- Knee flex: 20–35°
- Follow-through: >180°

---

## Stage 4: HuggingFace Coaching Layer

- API: HuggingFace Inference API (serverless, no GPU management)
- Model: `mistralai/Mistral-7B-Instruct-v0.3` (subject to change — check HF for current best instruct model)
- Auth: Bearer token from `HF_API_TOKEN` env var
- Prompt: structured template with angle values + ideal ranges (see `ml-pipeline` agent)
- Response format: JSON array of exactly 3 strings
- Timeout: 30 seconds
- Fallback: if API fails, return generic coaching tips (don't crash)

---

## Known Constraints & Risks

| Risk | Status | Mitigation |
|---|---|---|
| MediaPipe CPU latency in Docker on macOS | Unvalidated — estimated 10–20s | Benchmark in Task 2; add to UI as expected wait |
| MediaPipe accuracy with fast swing speeds | Unvalidated | Average across frames; flag low-confidence results |
| HF free tier cold start latency | Known issue — can add 10–30s | Acceptable for v0.1; upgrade tier or switch model in v0.2 |
| Camera angle dependency | Known — bad angles break keypoints | Document required filming position in README |
| Video file size | Unknown — depends on phone/camera | Enforce 100MB max; add compression in v0.2 |
