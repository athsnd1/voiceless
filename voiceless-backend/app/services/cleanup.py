import shutil
import threading
import time

from app import store
from app.config import UPLOAD_DIR, OUTPUT_DIR

MAX_AGE_HOURS = 24
CHECK_EVERY_SECONDS = 60 * 60  # once an hour


def cleanup_once() -> None:
    for job_id in store.delete_expired_jobs(MAX_AGE_HOURS):
        for f in UPLOAD_DIR.glob(f"{job_id}.*"):
            f.unlink(missing_ok=True)
        shutil.rmtree(OUTPUT_DIR / job_id, ignore_errors=True)


def _loop() -> None:
    while True:
        try:
            cleanup_once()
        except Exception as e:
            print(f"Cleanup error: {e}")
        time.sleep(CHECK_EVERY_SECONDS)


def start_cleanup() -> None:
    threading.Thread(target=_loop, daemon=True).start()