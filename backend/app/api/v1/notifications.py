"""Notification endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services import notifications as notifications_service

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = notifications_service.list_notifications(db, user, unread_only, limit)
    return ok([NotificationOut.model_validate(n).model_dump(mode="json") for n in items])


@router.get("/notifications/unread-count")
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok({"count": notifications_service.unread_count(db, user)})


@router.post("/notifications/{notification_id}/read")
def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    notification = notifications_service.mark_read(db, user, notification_id)
    return ok(NotificationOut.model_validate(notification).model_dump(mode="json"))


@router.post("/notifications/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    notifications_service.mark_all_read(db, user)
    return ok({"message": "All notifications marked as read."})
