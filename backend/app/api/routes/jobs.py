from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import get_session, session_scope
from app.models.job import Job, JobInputType, JobStatus
from app.schemas.jobs import JobBase, JobCreateResponse, JobDetail, JobListResponse, JobLogEntry, YouTubeRequest
from app.schemas.results import PipelineResult
from app.services.logger import add_job_log, fetch_job_logs
from app.services.pipeline import VideoProcessingPipeline, create_job
from app.utils.files import save_upload

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/", response_model=JobListResponse)
def list_jobs(session: Session = Depends(get_session)) -> JobListResponse:
    jobs = session.exec(select(Job).order_by(Job.created_at.desc())).all()
    job_models = [
        JobBase(
            id=job.id,
            input_type=job.input_type,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
        )
        for job in jobs
    ]
    return JobListResponse(jobs=job_models)


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: str, session: Session = Depends(get_session)) -> JobDetail:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    logs = [
        JobLogEntry(created_at=log.created_at, level=log.level, message=log.message)
        for log in fetch_job_logs(job_id)
    ]
    return JobDetail(
        id=job.id,
        input_type=job.input_type,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
        source=job.source,
        logs=logs,
        result_path=job.result_path,
    )


@router.get("/{job_id}/results", response_model=PipelineResult)
def get_results(job_id: str, session: Session = Depends(get_session)) -> PipelineResult:
    job = session.get(Job, job_id)
    if not job or job.status != JobStatus.COMPLETED or not job.result_path:
        raise HTTPException(status_code=404, detail="Results not available")
    result_path = Path(job.result_path)
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result file missing")
    return PipelineResult.parse_file(result_path)


@router.post("/upload", response_model=JobCreateResponse, status_code=201)
def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> JobCreateResponse:
    if not file.filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only MP4 uploads are supported")

    try:
        saved_path = save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = create_job(JobInputType.UPLOAD, str(saved_path))
    pipeline = VideoProcessingPipeline()
    background_tasks.add_task(pipeline.process, job.id)
    return JobCreateResponse(job_id=job.id, status=job.status)


@router.post("/youtube", response_model=JobCreateResponse, status_code=201)
def submit_youtube(
    payload: YouTubeRequest,
    background_tasks: BackgroundTasks,
) -> JobCreateResponse:
    if not settings.allow_youtube_downloads:
        raise HTTPException(status_code=403, detail="YouTube processing disabled")

    job = create_job(JobInputType.YOUTUBE, payload.url)
    background_tasks.add_task(_download_and_process_youtube, payload.url, job.id)
    return JobCreateResponse(job_id=job.id, status=job.status)


def _download_and_process_youtube(url: str, job_id: str) -> None:
    from tempfile import NamedTemporaryFile

    add_job_log(job_id, "Downloading YouTube video")
    try:
        try:
            from pytube import YouTube  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'pytube' package is required for YouTube downloads. Install via `pip install -e .[full]`."
            ) from exc

        video = YouTube(url)
        stream = video.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
        if not stream:
            raise RuntimeError("No compatible MP4 stream found")
        with NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            stream.download(filename=tmp_file.name)
            temp_path = Path(tmp_file.name)

        target_path = settings.upload_dir / f"{job_id}.mp4"
        shutil.move(str(temp_path), target_path)

        with session_scope() as session:
            job = session.get(Job, job_id)
            if job:
                job.source = str(target_path)
                job.updated_at = datetime.utcnow()

        add_job_log(job_id, "YouTube video downloaded")

        pipeline = VideoProcessingPipeline()
        pipeline.process(job_id)
    except Exception as exc:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(exc)
                job.updated_at = datetime.utcnow()
        add_job_log(job_id, f"YouTube download failed: {exc}", level="ERROR")
        raise
