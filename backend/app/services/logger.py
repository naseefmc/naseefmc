from __future__ import annotations

from sqlmodel import select

from app.db.session import session_scope
from app.models.job import JobLog


def add_job_log(job_id: str, message: str, level: str = "INFO") -> None:
    with session_scope() as session:
        session.add(JobLog(job_id=job_id, message=message, level=level))


def fetch_job_logs(job_id: str) -> list[JobLog]:
    with session_scope() as session:
        statement = select(JobLog).where(JobLog.job_id == job_id).order_by(JobLog.created_at.asc())
        return list(session.exec(statement))
