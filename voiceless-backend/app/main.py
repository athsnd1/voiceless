from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import store

from app.routers import jobs

from contextlib import asynccontextmanager
from app.services import cleanup

from app.config import ALLOWED_ORIGINS

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup.start_cleanup()
    yield


app = FastAPI(title="Voiceless", lifespan=lifespan)

store.init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)


@app.get("/")
def root():
    return {"status": "ok"}