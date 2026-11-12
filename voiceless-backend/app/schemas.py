from enum import Enum
from pydantic import BaseModel


class JobState(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class Job(BaseModel):
    job_id: str
    filename: str
    state: JobState = JobState.queued
    error: str | None = None