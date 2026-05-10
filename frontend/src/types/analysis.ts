export interface AnalysisAngles {
  elbow_angle: number;
  shoulder_rotation: number;
  knee_flex: number;
  hip_turn: number;
  follow_through: number;
}

export interface CoachingTip {
  angle_name: string;
  severity: "good" | "warning" | "critical";
  observation: string;
  drill: string;
}

export interface KeyFrame {
  label: "contact" | "windup" | "follow_through";
  image_b64: string;
  annotated_image_b64: string;
}

export interface AnalysisResult {
  status: "success";
  processing_time_seconds: number;
  keypoints_extracted: number;
  angles: AnalysisAngles;
  tips: CoachingTip[];
  key_frames: KeyFrame[];
}

export interface ApiError {
  status: "error";
  message: string;
}

export type AnalysisState =
  | { phase: "idle" }
  | { phase: "uploading" }
  | { phase: "processing" }
  | { phase: "done"; result: AnalysisResult }
  | { phase: "error"; message: string };
