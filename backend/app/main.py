from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import jobs
from app.core.config import settings
from app.db.session import init_db

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Video Intelligence Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    settings.storage_root.mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["System"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
