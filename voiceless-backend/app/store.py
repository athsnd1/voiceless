from app.schemas import Job

jobs: dict[str, Job] = {}


def add_job(job: Job) -> None:
    jobs[job.job_id] = job


def get_job(job_id: str) -> Job | None:
    return jobs.get(job_id)