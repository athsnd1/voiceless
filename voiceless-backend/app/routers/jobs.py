import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.schemas import Job
from app import store

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
    return job

@router.get("/{job_id}", response_model=Job)
def get_job_status(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job