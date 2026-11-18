# Voiceless

Upload a song and get the instrumental back. Voiceless uses the open-source
[Demucs](https://github.com/facebookresearch/demucs) model to separate vocals
from music, wrapped in a FastAPI backend and a React frontend.

## How it works

1. The React app uploads an audio file to the API.
2. The API saves it, creates a job and returns a job ID.
3. A background worker runs Demucs on the file, one job at a time.
4. The frontend polls the job status until it is done.
5. The instrumental can be played in the browser or downloaded as a WAV file.

## Tech stack

- **Backend:** Python 3.11, FastAPI, Uvicorn, SQLite, Demucs (PyTorch)
- **Frontend:** React, Tailwind CSS, TanStack Query, Axios, React Hot Toast

## Requirements

- Python 3.11 (64-bit)
- Node.js
- ffmpeg available on your PATH

## Setup

### Backend

```bash
cd voiceless-backend
python -m venv venv311
venv311\Scripts\activate        # Windows PowerShell: .\venv311\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000, with interactive docs at `/docs`.
The first separation downloads the Demucs model, which is a one-time download.

### Frontend

```bash
cd voiceless-frontend
pnpm install
pnpm run dev
```

Open http://localhost:5173. The backend only allows requests from this address.

## API

| Method | Endpoint                    | Description                                   |
| ------ | --------------------------- | --------------------------------------------- |
| POST   | `/jobs`                     | Upload an audio file and start a job          |
| GET    | `/jobs/{job_id}`            | Get job status: queued, processing, done, failed |
| GET    | `/jobs/{job_id}/instrumental` | Download the instrumental (only when done)  |

## Project structure

```
backend/
├── app/
│   ├── main.py            # app setup, CORS, startup tasks
│   ├── config.py          # paths and limits
│   ├── schemas.py         # job models
│   ├── store.py           # SQLite job storage
│   ├── routers/jobs.py    # API endpoints
│   └── services/
│       ├── separator.py   # Demucs separation
│       ├── worker.py      # one-at-a-time job queue
│       └── cleanup.py     # deletes old jobs and files
└── storage/               # uploads, outputs and the database (git-ignored)
```

## Limits and notes

- Supported formats: mp3, wav, flac, m4a, ogg. Maximum upload size is 25 MB.
- Separation runs on the CPU, so a full song takes several minutes.
- Only one song is processed at a time; others wait in the queue.
- Finished jobs and their files are deleted automatically after 24 hours.
- Only use music you have the rights to process. If you host this publicly,
  consider the copyright implications of storing and serving users' music.