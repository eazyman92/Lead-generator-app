import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from jobs.models import JobSnapshot


class InternalApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class InternalApiClient:
    """Async wrapper around backend internal job APIs."""

    def __init__(self, base_url: str, internal_api_token: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.internal_api_token = internal_api_token
        self.timeout_seconds = timeout_seconds

    async def claim_job(self, worker_id: str) -> JobSnapshot | None:
        data = await self._request(
            "POST",
            "/internal/v1/jobs/claim",
            {"worker_id": worker_id},
        )
        job = data.get("job")
        return JobSnapshot.from_api(job) if job else None

    async def complete_job(self, job_id: str, worker_id: str) -> JobSnapshot:
        data = await self._request(
            "POST",
            f"/internal/v1/jobs/{job_id}/complete",
            {"worker_id": worker_id},
        )
        return JobSnapshot.from_api(data["job"])

    async def fail_job(
        self,
        job_id: str,
        worker_id: str,
        error_code: str,
        error_message: str,
        retryable: bool,
        retry_delay_seconds: int,
    ) -> JobSnapshot:
        data = await self._request(
            "POST",
            f"/internal/v1/jobs/{job_id}/fail",
            {
                "worker_id": worker_id,
                "error_code": error_code,
                "error_message": error_message,
                "retryable": retryable,
                "retry_delay_seconds": retry_delay_seconds,
            },
        )
        return JobSnapshot.from_api(data["job"])

    async def get_job(self, job_id: str) -> JobSnapshot:
        data = await self._request("GET", f"/internal/v1/jobs/{job_id}", None)
        return JobSnapshot.from_api(data["job"])

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        request_id = str(uuid4())
        return await asyncio.to_thread(
            self._request_sync,
            method,
            path,
            payload,
            request_id,
        )

    def _request_sync(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        request_id: str,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Content-Type": "application/json",
                "X-Internal-API-Token": self.internal_api_token,
                "X-Request-ID": request_id,
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise self._error_from_http(exc) from exc
        except URLError as exc:
            raise InternalApiError(503, "BACKEND_UNAVAILABLE", str(exc)) from exc

        if response_payload.get("success") is not True:
            error = response_payload.get("error", {})
            raise InternalApiError(
                500,
                error.get("code", "INTERNAL_API_ERROR"),
                error.get("message", "Internal API call failed."),
            )
        return response_payload["data"]

    def _error_from_http(self, exc: HTTPError) -> InternalApiError:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            error = payload.get("error", {})
            return InternalApiError(
                exc.code,
                error.get("code", "INTERNAL_API_ERROR"),
                error.get("message", "Internal API call failed."),
            )
        except Exception:
            return InternalApiError(exc.code, "INTERNAL_API_ERROR", "Internal API call failed.")
