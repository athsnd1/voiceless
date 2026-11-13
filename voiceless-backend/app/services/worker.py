from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import store
from app.schemas import JobState
from app.services.separator import separate, SeparationError

# One worker means one separation at a time. Other jobs wait in line.
executor = ThreadPoolExecutor(max_workers=1)


def run_job(job_id: str, input_path: Path) -> None:
    job = store.get_job(job_id)
    if job is None:
        return

    job.state = JobState.processing
    try:
        separate(input_path)
        job.state = JobState.done
    except SeparationError as e:
        job.state = JobState.failed
        job.error = str(e)[:500]


def submit_job(job_id: str, input_path: Path) -> None:
    executor.submit(run_job, job_id, input_path)