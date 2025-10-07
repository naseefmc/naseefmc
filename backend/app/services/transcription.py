from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from app.schemas.results import TranscriptSegment

logger = logging.getLogger(__name__)


class Transcriber:
    """Abstract transcriber interface."""

    def transcribe(self, audio_path: Path) -> List[TranscriptSegment]:  # pragma: no cover - interface
        raise NotImplementedError


class WhisperTranscriber(Transcriber):
    """Transcriber implementation using OpenAI Whisper."""

    def __init__(self, model_name: str = "base") -> None:
        try:
            import whisper  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'whisper' package is required for WhisperTranscriber. Install via `pip install -e .[full]`."
            ) from exc

        self._whisper = whisper.load_model(model_name)

    def transcribe(self, audio_path: Path) -> List[TranscriptSegment]:
        result = self._whisper.transcribe(str(audio_path))
        segments = [
            TranscriptSegment(start=s["start"], end=s["end"], text=s["text"].strip())
            for s in result.get("segments", [])
        ]
        if not segments:
            segments = [TranscriptSegment(start=0.0, end=result.get("duration", 0.0), text=result.get("text", ""))]
        return segments


class StubTranscriber(Transcriber):
    """Fallback transcriber that returns placeholder results."""

    def transcribe(self, audio_path: Path) -> List[TranscriptSegment]:  # pragma: no cover - deterministic simple logic
        logger.warning("Using StubTranscriber - install Whisper for real transcription.")
        return [
            TranscriptSegment(start=0.0, end=5.0, text="[Transcription unavailable: install Whisper]")
        ]
