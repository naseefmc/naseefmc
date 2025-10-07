# Video Intelligence Analyzer (VIA) Backend

This backend implements the core processing pipeline for the Video Intelligence Analyzer. It exposes a FastAPI service that accepts either a video upload or a YouTube URL and orchestrates the processing workflow to produce transcripts, object detections, merged analytics, and summaries.

## Features

- Upload MP4 videos up to the configured size limit.
- Register a YouTube URL for offline download and processing.
- Background processing pipeline with detailed status tracking.
- Modular service layer with pluggable implementations for transcription, object detection, and summarisation.
- Storage of raw uploads, intermediate artefacts, and final analytics bundles.
- REST API for retrieving job metadata and results.

## Getting Started

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Real transcription and detection require optional dependencies. Install them with:

```bash
pip install -e .[full]
```

Set up environment variables in a `.env` file if required (see `app/core/config.py`).

## Project Layout

```
backend/
├── app/
│   ├── api/             # FastAPI routers
│   ├── core/            # Configuration and bootstrap logic
│   ├── db/              # Database models and session helpers
│   ├── models/          # SQLModel ORM classes
│   ├── schemas/         # Pydantic schemas for API IO and results
│   ├── services/        # Pipeline, detectors, transcription, summarisation
│   └── utils/           # Helper utilities
├── storage/             # Uploads, temporary files, pipeline outputs
├── README.md
└── pyproject.toml
```

## API Overview

- `POST /videos/upload` — Upload an MP4 file and start processing.
- `POST /videos/youtube` — Submit a YouTube URL for processing.
- `GET /jobs` — List jobs with current status.
- `GET /jobs/{job_id}` — Fetch a single job record.
- `GET /jobs/{job_id}/results` — Download pipeline results.

Refer to the OpenAPI docs at `/docs` after starting the service.
