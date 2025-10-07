from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from app.schemas.results import ObjectDetection

logger = logging.getLogger(__name__)


class ObjectDetector:
    """Abstract object detector."""

    def detect(self, video_path: Path) -> List[ObjectDetection]:  # pragma: no cover - interface
        raise NotImplementedError


class UltralyticsDetector(ObjectDetector):
    """YOLOv8 detector using Ultralytics."""

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.25) -> None:
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'ultralytics' package is required for UltralyticsDetector. Install via `pip install -e .[full]`."
            ) from exc

        self._model = YOLO(model_name)
        self._confidence = confidence

    def detect(self, video_path: Path) -> List[ObjectDetection]:  # pragma: no cover - heavy inference
        results = self._model.predict(source=str(video_path), stream=True, conf=self._confidence)
        detections: List[ObjectDetection] = []
        timestamp = 0.0
        frame_index = 0
        for result in results:
            if getattr(result, "speed", None) and result.speed.get("fps"):
                fps = result.speed["fps"]
                timestamp = frame_index / fps
            else:
                timestamp += 1.0
            frame_index += 1
            for box in result.boxes:
                cls_idx = int(box.cls.item())
                label = self._model.names.get(cls_idx, str(cls_idx))
                confidence = float(box.conf.item())
                detections.append(
                    ObjectDetection(
                        timestamp=timestamp,
                        label=label,
                        confidence=confidence,
                        instance_id=int(box.id.item()) if getattr(box, "id", None) is not None else None,
                    )
                )
        return detections


class StubDetector(ObjectDetector):
    """Fallback detector returning no detections."""

    def detect(self, video_path: Path) -> List[ObjectDetection]:  # pragma: no cover - deterministic simple logic
        logger.warning("Using StubDetector - install Ultralytics for real detections.")
        return []
