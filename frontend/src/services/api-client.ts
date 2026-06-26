import type {
  ApiEnvelope,
  ApiErrorCode,
  ApiErrorEnvelope,
  BusinessSearchResponse,
  JobStatus,
  SearchPayload,
  User
} from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const CSRF_COOKIE_NAME = "csrf_token";
const CSRF_HEADER_NAME = "X-CSRF-Token";

export class ApiClientError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;

  constructor(code: ApiErrorCode, message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
  }
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const cookies = document.cookie.split(";").map((cookie) => cookie.trim());
  const match = cookies.find((cookie) => cookie.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=").slice(1).join("=")) : null;
}

function errorCodeForStatus(status: number): ApiErrorCode {
  if (status === 401) return "UNAUTHENTICATED";
  if (status === 403) return "FORBIDDEN";
  if (status === 404) return "NOT_FOUND";
  if (status === 422) return "VALIDATION_ERROR";
  if (status === 429) return "RATE_LIMITED";
  if (status >= 500) return "SERVER_ERROR";
  return "NETWORK_ERROR";
}

async function parseError(response: Response): Promise<ApiClientError> {
  try {
    const payload = (await response.json()) as ApiErrorEnvelope;
    return new ApiClientError(
      errorCodeForStatus(response.status),
      payload.error?.message ?? "Request failed.",
      response.status
    );
  } catch {
    return new ApiClientError(
      errorCodeForStatus(response.status),
      "Request failed.",
      response.status
    );
  }
}

async function ensureCsrf(): Promise<string | null> {
  const existing = readCookie(CSRF_COOKIE_NAME);
  if (existing) {
    return existing;
  }
  await fetch(`${API_BASE_URL}/api/v1/auth/csrf`, {
    credentials: "include"
  });
  return readCookie(CSRF_COOKIE_NAME);
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retryOnAuth = true
): Promise<T> {
  const method = options.method?.toUpperCase() ?? "GET";
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");

  if (method !== "GET" && method !== "HEAD") {
    headers.set("Content-Type", "application/json");
    const csrfToken = await ensureCsrf();
    if (csrfToken) {
      headers.set(CSRF_HEADER_NAME, csrfToken);
    }
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      method,
      headers,
      credentials: "include"
    });
  } catch {
    throw new ApiClientError("NETWORK_ERROR", "Unable to reach the API.", 0);
  }

  if (response.status === 401 && retryOnAuth) {
    await refreshSession();
    return request<T>(path, options, false);
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  const envelope = (await response.json()) as ApiEnvelope<T>;
  return envelope.data;
}

export async function refreshSession() {
  await request<Record<string, never>>(
    "/api/v1/auth/refresh",
    { method: "POST" },
    false
  );
}

export async function getCurrentUser(): Promise<User> {
  const data = await request<{ user: User }>("/api/v1/auth/me");
  return data.user;
}

export async function login(email: string, password: string): Promise<User> {
  const data = await request<{ user: User }>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  return data.user;
}

export async function logout(): Promise<void> {
  await request<Record<string, never>>(
    "/api/v1/auth/logout",
    { method: "POST" },
    false
  );
}

export async function searchBusinesses(
  payload: SearchPayload
): Promise<BusinessSearchResponse> {
  return request<BusinessSearchResponse>("/api/v1/search", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`/api/job-status/${jobId}`, {
    credentials: "include"
  });
  if (!response.ok) {
    throw new ApiClientError(
      errorCodeForStatus(response.status),
      "Unable to load job status.",
      response.status
    );
  }
  const envelope = (await response.json()) as ApiEnvelope<{ job: JobStatus }>;
  return envelope.data.job;
}

export function userFriendlyError(error: unknown): string {
  if (!(error instanceof ApiClientError)) {
    return "Something went wrong. Please try again.";
  }
  const messages: Record<ApiErrorCode, string> = {
    UNAUTHENTICATED: "Your session expired. Please sign in again.",
    FORBIDDEN: "You do not have permission to perform this action.",
    NOT_FOUND: "The requested resource was not found.",
    VALIDATION_ERROR: "Check the highlighted fields and try again.",
    RATE_LIMITED: "Too many requests. Please wait a moment and retry.",
    SERVER_ERROR: "The server could not complete the request.",
    NETWORK_ERROR: "Unable to connect to the API."
  };
  return messages[error.code] ?? error.message;
}
