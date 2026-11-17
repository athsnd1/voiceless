import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
OUTPUT_DIR = BASE_DIR / "storage" / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}

DB_PATH = BASE_DIR / "storage" / "jobs.db"

MAX_UPLOAD_MB = 25
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

MAX_ACTIVE_PER_IP = 1
MAX_QUEUED_JOBS = 5