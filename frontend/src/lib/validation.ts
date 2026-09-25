export const UPLOAD_LIMITS = {
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024, // 10MB
  MIN_DIMENSION: 64,
  MAX_DIMENSION: 4096,
  ALLOWED_MIME_TYPES: ["image/png", "image/jpeg", "image/jpg"],
};

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

export function validateUploadFile(file: { size: number; type: string }): FileValidationResult {
  if (file.size <= 0) {
    return { valid: false, error: "Uploaded file is empty (0 bytes)." };
  }
  if (file.size > UPLOAD_LIMITS.MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      error: `File size exceeds the 10MB limit (${(file.size / (1024 * 1024)).toFixed(2)}MB).`,
    };
  }
  if (!UPLOAD_LIMITS.ALLOWED_MIME_TYPES.includes(file.type.toLowerCase())) {
    return {
      valid: false,
      error: `Unsupported file format '${file.type}'. Please upload a PNG or JPEG radiograph.`,
    };
  }
  return { valid: true };
}

export function validateImageDimensions(width: number, height: number): FileValidationResult {
  if (
    width < UPLOAD_LIMITS.MIN_DIMENSION ||
    height < UPLOAD_LIMITS.MIN_DIMENSION ||
    width > UPLOAD_LIMITS.MAX_DIMENSION ||
    height > UPLOAD_LIMITS.MAX_DIMENSION
  ) {
    return {
      valid: false,
      error: `Image dimensions (${width}x${height}) must be between ${UPLOAD_LIMITS.MIN_DIMENSION}px and ${UPLOAD_LIMITS.MAX_DIMENSION}px.`,
    };
  }
  return { valid: true };
}

export interface ReviewFormPayload {
  doctor_verdict: string;
  doctor_explanation: string;
  recommendation: string;
}

export function validateReviewForm(payload: ReviewFormPayload): { valid: boolean; error?: string } {
  if (!payload.doctor_verdict || !payload.doctor_verdict.trim()) {
    return { valid: false, error: "Diagnostic verdict selection is mandatory." };
  }
  if (!payload.doctor_explanation || payload.doctor_explanation.trim().length < 5) {
    return { valid: false, error: "Clinical explanation must be at least 5 characters." };
  }
  if (!payload.recommendation || payload.recommendation.trim().length < 5) {
    return { valid: false, error: "Clinical recommendation must be at least 5 characters." };
  }
  return { valid: true };
}

export function computeRiskBand(probability: number): "Low Risk" | "Borderline" | "High Risk" {
  if (probability >= 0.60) {
    return "High Risk";
  }
  if (probability >= 0.35) {
    return "Borderline";
  }
  return "Low Risk";
}
