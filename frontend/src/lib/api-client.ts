import {
  CaseResponse,
  CaseReviewRequest,
  DashboardStats,
  HealthResponse,
  PaginatedCasesResponse,
  TokenResponse,
  UserLoginRequest,
  UserPublic,
  UserRegisterRequest,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let inMemoryAccessToken: string | null = null;
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setAccessToken(token: string | null) {
  inMemoryAccessToken = token;
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (inMemoryAccessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${inMemoryAccessToken}`);
  }

  // Set credentials for httpOnly cookies
  const fetchOptions: RequestInit = {
    ...options,
    headers,
    credentials: "include",
  };

  let response = await fetch(url, fetchOptions);

  // Handle 401 Silent Refresh
  if (response.status === 401 && !endpoint.includes("/auth/login") && !endpoint.includes("/auth/refresh")) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const refreshRes = await fetch(`${API_BASE}/api/auth/refresh`, {
          method: "POST",
          credentials: "include",
        });

        if (refreshRes.ok) {
          const refreshData: TokenResponse = await refreshRes.json();
          setAccessToken(refreshData.access_token);
          isRefreshing = false;
          onRefreshed(refreshData.access_token);

          // Retry initial request with new token
          headers.set("Authorization", `Bearer ${refreshData.access_token}`);
          return fetch(url, { ...fetchOptions, headers }).then((res) => {
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            return res.json() as Promise<T>;
          });
        } else {
          setAccessToken(null);
          isRefreshing = false;
        }
      } catch (err) {
        setAccessToken(null);
        isRefreshing = false;
      }
    } else {
      // Queue requests while refresh is in-flight
      return new Promise<T>((resolve, reject) => {
        addRefreshSubscriber(async (newToken) => {
          headers.set("Authorization", `Bearer ${newToken}`);
          try {
            const retryRes = await fetch(url, { ...fetchOptions, headers });
            if (!retryRes.ok) throw new Error(`HTTP error ${retryRes.status}`);
            resolve((await retryRes.json()) as T);
          } catch (e) {
            reject(e);
          }
        });
      });
    }
  }

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export function getMediaUrl(pathOrCaseId?: string | number | null, type?: "original" | "gradcam"): string {
  if (!pathOrCaseId) return "";
  const token = getAccessToken();
  const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : "";

  if (type) {
    return `${API_BASE}/api/media/${pathOrCaseId}/${type}${tokenQuery}`;
  }

  const str = String(pathOrCaseId);
  if (str.startsWith("http")) {
    return str.includes("?token=") ? str : `${str}${tokenQuery}`;
  }

  const cleanPath = str.startsWith("/") ? str : `/${str}`;
  return `${API_BASE}${cleanPath}${cleanPath.includes("?") ? `&token=${encodeURIComponent(token || "")}` : tokenQuery}`;
}

export const authApi = {
  register: (payload: UserRegisterRequest) =>
    fetchApi<UserPublic>("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  login: async (payload: UserLoginRequest) => {
    const data = await fetchApi<TokenResponse>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setAccessToken(data.access_token);
    return data;
  },

  refresh: async () => {
    const data = await fetchApi<TokenResponse>("/api/auth/refresh", {
      method: "POST",
    });
    setAccessToken(data.access_token);
    return data;
  },

  logout: async () => {
    try {
      await fetchApi<{ message: string }>("/api/auth/logout", {
        method: "POST",
      });
    } finally {
      setAccessToken(null);
    }
  },

  getMe: () => fetchApi<UserPublic>("/api/me"),
};

export const casesApi = {
  submitCase: async (file: File): Promise<CaseResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const headers = new Headers();
    if (inMemoryAccessToken) {
      headers.set("Authorization", `Bearer ${inMemoryAccessToken}`);
    }

    const response = await fetch(`${API_BASE}/api/cases`, {
      method: "POST",
      headers,
      body: formData,
      credentials: "include",
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Failed submitting case");
    }

    const data: CaseResponse = await response.json();
    // Normalize aliases
    data.predicted_class = data.model_prediction;
    data.calibrated_probability = data.cancer_probability;
    data.original_image_path = data.image_url;
    data.gradcam_path = data.gradcam_url;
    return data;
  },

  listCases: async (page = 1, limit = 20, status?: string): Promise<PaginatedCasesResponse> => {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (status) params.append("status", status);
    const res = await fetchApi<PaginatedCasesResponse>(`/api/cases?${params.toString()}`);
    res.items = res.items.map((item) => ({
      ...item,
      predicted_class: item.model_prediction,
      calibrated_probability: item.cancer_probability,
      original_image_path: item.image_url,
      gradcam_path: item.gradcam_url,
    }));
    return res;
  },

  getCase: async (id: string | number): Promise<CaseResponse> => {
    const item = await fetchApi<CaseResponse>(`/api/cases/${id}`);
    item.predicted_class = item.model_prediction;
    item.calibrated_probability = item.cancer_probability;
    item.original_image_path = item.image_url;
    item.gradcam_path = item.gradcam_url;
    return item;
  },

  reviewCase: (id: string | number, payload: CaseReviewRequest) =>
    fetchApi<CaseResponse>(`/api/cases/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getStats: () => fetchApi<DashboardStats>("/api/cases/stats"),

  getMediaUrl: (pathOrCaseId?: string | number | null, type?: "original" | "gradcam") =>
    getMediaUrl(pathOrCaseId, type),

  downloadPdfReport: async (caseId: string | number): Promise<Blob> => {
    const headers = new Headers();
    if (inMemoryAccessToken) {
      headers.set("Authorization", `Bearer ${inMemoryAccessToken}`);
    }
    const response = await fetch(`${API_BASE}/api/cases/${caseId}/report.pdf`, {
      headers,
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`Failed to generate PDF report (HTTP ${response.status})`);
    }
    return response.blob();
  },
};

export const healthApi = {
  check: () => fetchApi<HealthResponse>("/health"),
};

// Unified api object for seamless imports across pages
export const api = {
  login: authApi.login,
  register: authApi.register,
  logout: authApi.logout,
  getMe: authApi.getMe,
  submitCase: casesApi.submitCase,
  getCases: (opts?: { page?: number; limit?: number; status?: string }) =>
    casesApi.listCases(opts?.page || 1, opts?.limit || 20, opts?.status),
  getCase: casesApi.getCase,
  submitReview: (id: string | number, payload: CaseReviewRequest) => casesApi.reviewCase(id, payload),
  getDashboardStats: casesApi.getStats,
  downloadPdfReport: casesApi.downloadPdfReport,
  getMediaUrl,
  checkHealth: healthApi.check,
};
