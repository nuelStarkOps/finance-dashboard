"""Notifications service — in-app notification records.

Includes the idempotent daily "file your expenses" reminder. Reminders are
generated lazily when notifications are read; a real scheduler (APScheduler)
and email delivery (SES) are later refinements.
"""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User

DAILY_FILING_TYPE = "daily_filing"


def _start_of_day(now: datetime) -> datetime:
    return datetime(now.year, now.month, now.day, tzinfo=UTC)


def ensure_daily_filing_reminder(db: Session, user: User) -> None:
    """Create today's 'file expenses' reminder if it does not already exist."""
    start = _start_of_day(datetime.now(UTC))
    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == user.id,
            Notification.type == DAILY_FILING_TYPE,
            Notification.created_at >= start,
        )
        .first()
    )
    if existing is None:
        db.add(
            Notification(
                user_id=user.id,
                type=DAILY_FILING_TYPE,
                title="File today's expenses",
                message="Remember to record today's income and expenses to keep your dashboard accurate.",
            )
        )
        db.commit()


def list_notifications(
    db: Session, user: User, unread_only: bool = False, limit: int = 50
) -> list[Notification]:
    ensure_daily_filing_reminder(db, user)
    query = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    return query.all()


def unread_count(db: Session, user: User) -> int:
    ensure_daily_filing_reminder(db, user)
    return int(
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user.id, Notification.read_at.is_(None))
        .scalar()
        or 0
    )


def mark_read(db: Session, user: User, notification_id: uuid.UUID) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        db.commit()
    return notification


def mark_all_read(db: Session, user: User) -> None:
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.read_at.is_(None)
    ).update({"read_at": datetime.now(UTC)})
    db.commit()
