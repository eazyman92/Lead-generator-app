export type ApiErrorCode =
  | "UNAUTHENTICATED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "VALIDATION_ERROR"
  | "RATE_LIMITED"
  | "SERVER_ERROR"
  | "NETWORK_ERROR";

export type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  message: string | null;
  request_id: string;
};

export type ApiErrorEnvelope = {
  success: false;
  error: {
    code: string;
    message: string;
  };
  request_id?: string;
};

export type User = {
  id: string;
  email: string;
  role: "admin" | "user";
};

export type Pagination = {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type BusinessSearchResult = {
  id: string;
  name: string;
  industry: string;
  website: string;
  phone: string;
  email: string | null;
  country: string;
  state: string;
  city: string;
  address: string;
  source_type: string;
};

export type BusinessSearchResponse = {
  results: BusinessSearchResult[];
  pagination: Pagination;
  job: {
    id: string;
    type: "contact_collection";
  } | null;
};

export type SearchPayload = {
  filters: {
    industry: string;
    country: string;
    state: string;
    city: string;
  };
  pagination: {
    page: number;
    per_page: number;
  };
};

export type JobStage =
  | "idle"
  | "created"
  | "processing"
  | "completed"
  | "failed";

export type JobStatus = {
  id: string;
  job_type: string;
  status: "pending" | "running" | "completed" | "failed";
  attempts: number;
  max_attempts: number;
  dead_letter: boolean;
  dead_letter_reason: string | null;
  error_message: string | null;
};
