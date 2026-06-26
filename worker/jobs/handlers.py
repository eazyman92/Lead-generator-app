from typing import Protocol

from jobs.models import HandlerResult, JobSnapshot


class JobHandler(Protocol):
    async def handle(self, job: JobSnapshot) -> HandlerResult:
        """Execute a claimed job and return the lifecycle result."""


class InterfaceOnlyHandler:
    """Placeholder for Phase 4A infrastructure before domain logic is implemented."""

    async def handle(self, job: JobSnapshot) -> HandlerResult:
        return HandlerResult.failed(
            error_code="INVALID_PAYLOAD",
            error_message=(
                f"{job.job_type} handler interface is registered, "
                "but business logic is not implemented in this phase."
            ),
            retryable=False,
        )


def default_handlers() -> dict[str, JobHandler]:
    return {
        "contact_collection": InterfaceOnlyHandler(),
        "csv_export": InterfaceOnlyHandler(),
    }
