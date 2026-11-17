from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import store
from app.schemas import JobState
from app.services.separator import separate, SeparationError

# One worker means one separation at a time. Other jobs wait in line.
executor = ThreadPoolExecutor(max_workers=1)


def run_job(job_id: str, input_path: Path) -> None:
    store.update_job(job_id, JobState.processing)
    try:
        separate(input_path)
        store.update_job(job_id, JobState.done)
    except SeparationError as e:
        store.update_job(job_id, JobState.failed, str(e)[:500])


def submit_job(job_id: str, input_path: Path) -> None:
    executor.submit(run_job, job_id, input_path)