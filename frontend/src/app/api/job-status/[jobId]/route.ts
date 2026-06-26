import { NextResponse } from "next/server";

const INTERNAL_BASE_URL =
  process.env.BACKEND_INTERNAL_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const internalToken = process.env.INTERNAL_API_TOKEN;
  if (!internalToken) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: "JOB_STATUS_UNAVAILABLE",
          message: "Job status polling is not configured."
        }
      },
      { status: 503 }
    );
  }

  const { jobId } = await params;
  const response = await fetch(
    `${INTERNAL_BASE_URL}/internal/v1/jobs/${jobId}`,
    {
      headers: {
        "X-Internal-API-Token": internalToken,
        "X-Request-ID": crypto.randomUUID()
      },
      cache: "no-store"
    }
  );
  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
