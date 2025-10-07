from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from app.models.job import JobInputType, JobStatus


class JobLogEntry(BaseModel):
    created_at: datetime
    level: str
    message: str


class JobBase(BaseModel):
    id: str
    input_type: JobInputType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str]


class JobDetail(JobBase):
    source: str
    logs: List[JobLogEntry] = Field(default_factory=list)
    result_path: Optional[str]


class JobListResponse(BaseModel):
    jobs: List[JobBase]


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


class YouTubeRequest(BaseModel):
    url: HttpUrl
