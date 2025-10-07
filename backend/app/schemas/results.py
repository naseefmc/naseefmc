from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class ObjectDetection(BaseModel):
    timestamp: float
    label: str
    confidence: float
    instance_id: Optional[int] = None


class ObjectFrequency(BaseModel):
    label: str
    count: int


class CoOccurrenceEntry(BaseModel):
    labels: List[str]
    count: int


class SentimentPoint(BaseModel):
    timestamp: float
    sentiment: float


class TimelineEntry(BaseModel):
    timestamp: float
    transcript: Optional[str]
    objects: Dict[str, int]


class AnalyticsBundle(BaseModel):
    object_frequency: List[ObjectFrequency]
    co_occurrence: List[CoOccurrenceEntry]
    sentiment_trend: List[SentimentPoint]


class PipelineResult(BaseModel):
    transcript: List[TranscriptSegment]
    detections: List[ObjectDetection]
    timeline: List[TimelineEntry]
    analytics: AnalyticsBundle
    summary: str
