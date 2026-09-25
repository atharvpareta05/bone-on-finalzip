export type UserRole = "patient" | "doctor";

export interface UserPublic {
  id: number;
  username: string;
  role: UserRole;
  display_name: string;
  created_at?: string | null;
}

export interface UserRegisterRequest {
  username: string;
  password: string;
  display_name: string;
}

export interface UserLoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserPublic;
}

export type RiskBand = "High Risk" | "Borderline" | "Borderline / Indeterminate" | "Low Risk";

export type CaseStatus = "AI-analyzed" | "In review" | "Reviewed" | "Pending doctor review" | "pending" | "reviewed";

export interface CaseResponse {
  id: string;
  patient_id: number;
  patient_name?: string | null;
  image_url: string;
  gradcam_url?: string | null;
  model_prediction: string;
  cancer_probability: number;
  risk_band: RiskBand | string;
  status: CaseStatus | string;
  doctor_verdict?: string | null;
  doctor_explanation?: string | null;
  recommendation?: string | null;
  created_at: string;
  reviewed_at?: string | null;
  reviewed_by?: number | null;
  reviewed_by_doctor_id?: number | string | null;

  // Compatibility aliases
  predicted_class?: string;
  calibrated_probability?: number;
  original_image_path?: string;
  gradcam_path?: string | null;
}

export interface PaginatedCasesResponse {
  items: CaseResponse[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface CaseReviewRequest {
  doctor_verdict: string;
  doctor_explanation: string;
  recommendation: string;
}

export interface DashboardStats {
  pending_cases: number;
  reviewed_cases: number;
  high_risk_pending: number;
  total_cases: number;
  pending_count?: number;
  reviewed_count?: number;
  high_risk_count?: number;
  total_patients?: number;
  model_version: string;
  model_device?: string;
  device?: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | string;
  model_loaded: boolean;
  db_connected: boolean;
  device: string;
  timestamp: string;
}
