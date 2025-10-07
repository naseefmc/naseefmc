from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.db.session import session_scope
from app.models.job import Job, JobInputType, JobStatus
from app.schemas.results import PipelineResult
from app.services.analytics import build_analytics_bundle, build_timeline
from app.services.audio import AudioExtractor
from app.services.detection import ObjectDetector, StubDetector, UltralyticsDetector
from app.services.logger import add_job_log
from app.services.summarisation import OpenAISummariser, StubSummariser, Summariser
from app.services.transcription import StubTranscriber, Transcriber, WhisperTranscriber

logger = logging.getLogger(__name__)


@dataclass
class PipelineComponents:
    audio_extractor: AudioExtractor
    transcriber: Transcriber
    detector: ObjectDetector
    summariser: Summariser


class VideoProcessingPipeline:
    """Coordinates the VIA processing workflow."""

    def __init__(self, components: Optional[PipelineComponents] = None) -> None:
        self.components = components or self._build_default_components()

    def _build_default_components(self) -> PipelineComponents:
        audio_extractor = AudioExtractor()

        try:
            transcriber: Transcriber = WhisperTranscriber(model_name=settings.whisper_model)
        except Exception as exc:  # pragma: no cover - optional path
            logger.warning("Falling back to stub transcriber: %s", exc)
            transcriber = StubTranscriber()

        try:
            detector: ObjectDetector = UltralyticsDetector(model_name=settings.yolov8_model)
        except Exception as exc:  # pragma: no cover - optional path
            logger.warning("Falling back to stub detector: %s", exc)
            detector = StubDetector()

        if settings.openai_api_key:
            try:
                summariser: Summariser = OpenAISummariser(api_key=settings.openai_api_key)
            except Exception as exc:  # pragma: no cover - optional path
                logger.warning("Falling back to stub summariser: %s", exc)
                summariser = StubSummariser()
        else:
            summariser = StubSummariser()

        return PipelineComponents(
            audio_extractor=audio_extractor,
            transcriber=transcriber,
            detector=detector,
            summariser=summariser,
        )

    def process(self, job_id: str) -> None:
        logger.info("Starting pipeline for job %s", job_id)
        with session_scope() as session:
            job = session.get(Job, job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            job.status = JobStatus.PROCESSING
            job.updated_at = datetime.utcnow()
        add_job_log(job_id, "Pipeline started")

        try:
            result = self._run_pipeline(job_id)
            result_path = settings.result_dir / f"{job_id}.json"
            with result_path.open("w", encoding="utf-8") as fp:
                json.dump(result.dict(), fp, indent=2)

            with session_scope() as session:
                job = session.get(Job, job_id)
                if job:
                    job.status = JobStatus.COMPLETED
                    job.result_path = str(result_path)
                    job.updated_at = datetime.utcnow()
            add_job_log(job_id, "Pipeline completed successfully")
        except Exception as exc:
            logger.exception("Pipeline failed for job %s", job_id)
            with session_scope() as session:
                job = session.get(Job, job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = str(exc)
                    job.updated_at = datetime.utcnow()
            add_job_log(job_id, f"Pipeline failed: {exc}", level="ERROR")

    def _run_pipeline(self, job_id: str) -> PipelineResult:
        with session_scope() as session:
            job = session.get(Job, job_id)
            if not job:
                raise ValueError(f"Job {job_id} missing")
            source_path = Path(job.source)

        audio_path = settings.storage_root / "audio" / f"{job_id}.wav"
        add_job_log(job_id, "Extracting audio track")
        audio_file = self.components.audio_extractor.extract(source_path, audio_path)

        add_job_log(job_id, "Running speech transcription")
        transcript = self.components.transcriber.transcribe(audio_file)

        add_job_log(job_id, "Running object detection")
        detections = self.components.detector.detect(source_path)

        add_job_log(job_id, "Building analytics bundle")
        timeline = build_timeline(transcript, detections, settings.timeline_window)
        analytics = build_analytics_bundle(transcript, detections, settings.timeline_window, timeline)

        add_job_log(job_id, "Generating summary")
        summary = self.components.summariser.summarise(transcript, detections)

        return PipelineResult(
            transcript=transcript,
            detections=detections,
            timeline=timeline,
            analytics=analytics,
            summary=summary,
        )


def create_job(input_type: JobInputType, source: str) -> Job:
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    job = Job(id=job_id, input_type=input_type, source=source, created_at=now, updated_at=now)
    with session_scope() as session:
        session.add(job)
    add_job_log(job_id, f"Job created for {input_type.value}")
    return job
