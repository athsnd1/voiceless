from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import jobs

app = FastAPI(title="Voiceless")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)


@app.get("/")
def root():
    return {"status": "ok"}