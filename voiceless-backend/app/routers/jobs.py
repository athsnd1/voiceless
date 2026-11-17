import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from app.config import (
    UPLOAD_DIR, OUTPUT_DIR, ALLOWED_EXTENSIONS,
    MAX_UPLOAD_MB, MAX_UPLOAD_BYTES, MAX_ACTIVE_PER_IP, MAX_QUEUED_JOBS,
)

from app.config import UPLOAD_DIR, OUTPUT_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB, MAX_UPLOAD_BYTES
from app.schemas import Job
from app import store
from app.services.worker import submit_job

from fastapi.responses import FileResponse

from app.schemas import JobState


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("")
async def create_job(request: Request, file: UploadFile = File(...)):
    ip = request.client.host if request.client else "unknown"
    if store.count_active() >= MAX_QUEUED_JOBS:
        raise HTTPException(
            status_code=503,
            detail="The server is busy right now. Please try again in a few minutes.",
        )
    if store.count_active(ip) >= MAX_ACTIVE_PER_IP:
        raise HTTPException(
            status_code=429,
            detail="You already have a song processing. Please wait for it to finish.",
        )
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    job_id = uuid.uuid4().hex
    save_path = UPLOAD_DIR / f"{job_id}{ext}"

    size = 0
    try:
        with open(save_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum is {MAX_UPLOAD_MB} MB.",
                    )
                f.write(chunk)
    except Exception:
        save_path.unlink(missing_ok=True)  # don't leave a partial file behind
        raise

    job = Job(job_id=job_id, filename=file.filename or save_path.name)
    store.add_job(job, ip)
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