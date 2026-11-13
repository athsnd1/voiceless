import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.schemas import Job
from app import store
from app.services.worker import submit_job

from fastapi.responses import FileResponse

from app.config import OUTPUT_DIR
from app.schemas import JobState

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("")
async def create_job(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    job_id = uuid.uuid4().hex
    save_path = UPLOAD_DIR / f"{job_id}{ext}"

    with open(save_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1 MB at a time
            f.write(chunk)

    job = Job(job_id=job_id, filename=file.filename or save_path.name)
    store.add_job(job)
    submit_job(job_id, save_path)
    return job

@router.get("/{job_id}", response_model=Job)
def get_job_status(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/instrumental")
def download_instrumental(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.state != JobState.done:
        raise HTTPException(status_code=409, detail=f"Job is {job.state.value}, not done")

    path = OUTPUT_DIR / job_id / "no_vocals.wav"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file is missing")

    download_name = f"{Path(job.filename).stem} (instrumental).wav"
    return FileResponse(path, media_type="audio/wav", filename=download_name)