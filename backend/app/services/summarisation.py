from __future__ import annotations

import logging
from typing import List

from app.schemas.results import ObjectDetection, TranscriptSegment

logger = logging.getLogger(__name__)


class Summariser:
    """Abstract summariser."""

    def summarise(self, transcript: List[TranscriptSegment], detections: List[ObjectDetection]) -> str:  # pragma: no cover
        raise NotImplementedError


class OpenAISummariser(Summariser):
    """Summariser that delegates to the OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'openai' package is required for OpenAISummariser. Install via `pip install -e .[full]`."
            ) from exc

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def summarise(self, transcript: List[TranscriptSegment], detections: List[ObjectDetection]) -> str:  # pragma: no cover
        transcript_text = "\n".join(f"[{seg.start:.2f}-{seg.end:.2f}] {seg.text}" for seg in transcript)
        detection_text = "\n".join(
            f"{det.timestamp:.2f}s: {det.label} ({det.confidence:.2f})" for det in detections
        ) or "No detections"
        prompt = (
            "You are an analyst generating a concise report for a processed video."
            " Summarise the key narrative points and mention notable visual detections."
            " Use clear, factual language.\n\n"
            f"Transcript:\n{transcript_text}\n\nDetections:\n{detection_text}"
        )
        response = self._client.responses.create(model=self._model, input=prompt)
        return response.output[0].content[0].text.strip()


class StubSummariser(Summariser):
    def summarise(self, transcript: List[TranscriptSegment], detections: List[ObjectDetection]) -> str:
        logger.warning("Using StubSummariser - configure OpenAI for intelligent summaries.")
        if transcript:
            return (
                "Summary unavailable. Configure OpenAI credentials for automatic summarisation."
                f" First transcript segment: '{transcript[0].text[:120]}...'"
            )
        return "Summary unavailable. Configure OpenAI credentials for automatic summarisation."
