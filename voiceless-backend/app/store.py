import sqlite3
from contextlib import closing

from app.config import DB_PATH
from app.schemas import Job, JobState


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                state TEXT NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN client_ip TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
        # Jobs that were queued or running when the server stopped can never
        # finish, because the work queue lived in memory. Mark them failed.
        conn.execute(
            """
            UPDATE jobs
            SET state = 'failed', error = 'Server restarted before this job finished'
            WHERE state IN ('queued', 'processing')
            """
        )


def add_job(job: Job, client_ip: str | None = None) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO jobs (job_id, filename, state, error, client_ip) VALUES (?, ?, ?, ?, ?)",
            (job.job_id, job.filename, job.state.value, job.error, client_ip),
        )


def count_active(client_ip: str | None = None) -> int:
    """Count jobs that are queued or processing, optionally for one IP."""
    query = "SELECT COUNT(*) FROM jobs WHERE state IN ('queued', 'processing')"
    params: tuple = ()
    if client_ip is not None:
        query += " AND client_ip = ?"
        params = (client_ip,)
    with closing(_connect()) as conn:
        return conn.execute(query, params).fetchone()[0]


def get_job(job_id: str) -> Job | None:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT job_id, filename, state, error FROM jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    return Job(**dict(row)) if row else None


def update_job(job_id: str, state: JobState, error: str | None = None) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute(
            "UPDATE jobs SET state = ?, error = ? WHERE job_id = ?",
            (state.value, error, job_id),
        )
        
def delete_expired_jobs(max_age_hours: int) -> list[str]:
    """Delete finished or failed jobs older than max_age_hours. Returns their IDs."""
    with closing(_connect()) as conn, conn:
        rows = conn.execute(
            """
            SELECT job_id FROM jobs
            WHERE state IN ('done', 'failed')
              AND created_at < datetime('now', ?)
            """,
            (f"-{max_age_hours} hours",),
        ).fetchall()
        ids = [r["job_id"] for r in rows]
        conn.executemany("DELETE FROM jobs WHERE job_id = ?", [(i,) for i in ids])
    return ids