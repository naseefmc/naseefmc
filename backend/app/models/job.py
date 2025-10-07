from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Column, DateTime, Enum as SqlEnum, Field, SQLModel


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInputType(str, Enum):
    UPLOAD = "upload"
    YOUTUBE = "youtube"


class Job(SQLModel, table=True):
    id: str = Field(primary_key=True)
    input_type: JobInputType = Field(sa_column=Column(SqlEnum(JobInputType)))
    source: str = Field(description="File path or remote URL used for processing.")
    status: JobStatus = Field(default=JobStatus.PENDING, sa_column=Column(SqlEnum(JobStatus)))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    error_message: Optional[str] = Field(default=None)
    result_path: Optional[str] = Field(default=None, description="Filesystem path to the job result bundle.")


class JobLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="job.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    level: str = Field(default="INFO")
    message: str
