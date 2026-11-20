"""Category endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import categories as categories_service

router = APIRouter(tags=["categories"])


@router.get("/categories")
def list_categories(
    type: str | None = Query(default=None, pattern="^(INCOME|EXPENSE)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    categories = categories_service.list_categories(db, user, type)
    return ok([CategoryOut.model_validate(c).model_dump(mode="json") for c in categories])


@router.post("/categories")
def create_category(
    payload: CategoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    category = categories_service.create_category(db, user, payload)
    return ok(CategoryOut.model_validate(category).model_dump(mode="json"))


@router.patch("/categories/{category_id}")
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    category = categories_service.update_category(db, user, category_id, payload)
    return ok(CategoryOut.model_validate(category).model_dump(mode="json"))


@router.post("/categories/{category_id}/archive")
def archive_category(
    category_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    category = categories_service.archive_category(db, user, category_id)
    return ok(CategoryOut.model_validate(category).model_dump(mode="json"))
