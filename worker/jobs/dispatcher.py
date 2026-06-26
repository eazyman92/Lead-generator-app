from jobs.handlers import JobHandler
from jobs.models import HandlerResult, JobSnapshot


class JobDispatcher:
    def __init__(self, handlers: dict[str, JobHandler]) -> None:
        self.handlers = handlers

    async def dispatch(self, job: JobSnapshot) -> HandlerResult:
        handler = self.handlers.get(job.job_type)
        if handler is None:
            return HandlerResult.failed(
                error_code="UNKNOWN_JOB_TYPE",
                error_message=f"Unknown job type: {job.job_type}",
                retryable=False,
            )
        return await handler.handle(job)
