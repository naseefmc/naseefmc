from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Dict, Iterable, List, Optional

from app.schemas.results import (
    AnalyticsBundle,
    CoOccurrenceEntry,
    ObjectDetection,
    ObjectFrequency,
    SentimentPoint,
    TimelineEntry,
    TranscriptSegment,
)


def build_timeline(
    transcript: List[TranscriptSegment], detections: List[ObjectDetection], window: float
) -> List[TimelineEntry]:
    """Merge transcript segments and detections into a unified timeline."""

    timeline: List[TimelineEntry] = []
    for segment in transcript:
        start = segment.start - window / 2
        end = segment.end + window / 2
        window_detections = [
            detection
            for detection in detections
            if start <= detection.timestamp <= end
        ]
        object_counts: Dict[str, int] = Counter(det.label for det in window_detections)
        timeline.append(
            TimelineEntry(
                timestamp=segment.start,
                transcript=segment.text,
                objects=dict(object_counts),
            )
        )
    return timeline


def compute_object_frequency(detections: Iterable[ObjectDetection]) -> List[ObjectFrequency]:
    counter = Counter(det.label for det in detections)
    return [ObjectFrequency(label=label, count=count) for label, count in counter.most_common()]


def compute_co_occurrence(timeline: Iterable[TimelineEntry]) -> List[CoOccurrenceEntry]:
    pair_counter: Counter[tuple[str, ...]] = Counter()
    for entry in timeline:
        labels = [label for label, count in entry.objects.items() if count > 0]
        for combo in combinations(sorted(set(labels)), 2):
            pair_counter[combo] += 1
    return [CoOccurrenceEntry(labels=list(labels), count=count) for labels, count in pair_counter.most_common()]


def compute_sentiment(transcript: Iterable[TranscriptSegment]) -> List[SentimentPoint]:
    """Lightweight sentiment estimation using heuristics."""

    positive_keywords = {"good", "great", "excellent", "happy", "success", "win"}
    negative_keywords = {"bad", "poor", "sad", "fail", "loss", "danger"}
    results: List[SentimentPoint] = []
    for segment in transcript:
        words = set(segment.text.lower().split())
        score = 0.0
        if words & positive_keywords:
            score += 0.6
        if words & negative_keywords:
            score -= 0.6
        results.append(SentimentPoint(timestamp=segment.start, sentiment=score))
    return results


def build_analytics_bundle(
    transcript: List[TranscriptSegment],
    detections: List[ObjectDetection],
    window: float,
    timeline: Optional[List[TimelineEntry]] = None,
) -> AnalyticsBundle:
    timeline = timeline or build_timeline(transcript, detections, window)
    return AnalyticsBundle(
        object_frequency=compute_object_frequency(detections),
        co_occurrence=compute_co_occurrence(timeline),
        sentiment_trend=compute_sentiment(transcript),
    )
