"""Category service — default and custom income/expense categories."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import CategoryStatus
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate

#: Default system categories seeded by the Phase 2 migration.
DEFAULT_CATEGORIES: list[tuple[str, str, str, str]] = [
    ("Salary", "INCOME", "briefcase", "#34D399"),
    ("Freelance", "INCOME", "laptop", "#34D399"),
    ("Business", "INCOME", "store", "#34D399"),
    ("Investments", "INCOME", "trending-up", "#34D399"),
    ("Gifts", "INCOME", "gift", "#34D399"),
    ("Other Income", "INCOME", "plus", "#34D399"),
    ("Groceries", "EXPENSE", "shopping-cart", "#F87171"),
    ("Dining", "EXPENSE", "utensils", "#F87171"),
    ("Transport", "EXPENSE", "car", "#F87171"),
    ("Housing", "EXPENSE", "home", "#F87171"),
    ("Utilities", "EXPENSE", "zap", "#F87171"),
    ("Health", "EXPENSE", "heart", "#F87171"),
    ("Education", "EXPENSE", "book", "#F87171"),
    ("Entertainment", "EXPENSE", "film", "#F87171"),
    ("Shopping", "EXPENSE", "shopping-bag", "#F87171"),
    ("Bills", "EXPENSE", "file-text", "#F87171"),
    ("Subscriptions", "EXPENSE", "repeat", "#F87171"),
    ("Other Expense", "EXPENSE", "more-horizontal", "#F87171"),
]


def ensure_default_categories(db: Session) -> None:
    """Insert any missing system categories (idempotent)."""
    existing = {
        (c.type, c.name) for c in db.query(Category).filter(Category.is_system.is_(True)).all()
    }
    added = False
    for name, ctype, icon, color in DEFAULT_CATEGORIES:
        if (ctype, name) not in existing:
            db.add(
                Category(
                    user_id=None,
                    name=name,
                    type=ctype,
                    icon=icon,
                    color=color,
                    is_system=True,
                    status=CategoryStatus.ACTIVE.value,
                )
            )
            added = True
    if added:
        db.commit()


def list_categories(db: Session, user: User, type_filter: str | None = None) -> list[Category]:
    ensure_default_categories(db)
    query = db.query(Category).filter(
        Category.status == CategoryStatus.ACTIVE.value,
        (Category.user_id.is_(None)) | (Category.user_id == user.id),
    )
    if type_filter:
        query = query.filter(Category.type == type_filter)
    return query.order_by(Category.is_system.desc(), Category.name).all()


def get_owned_category(db: Session, user: User, category_id: uuid.UUID) -> Category:
    """Return a category that the user may use (their own or a system default)."""
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    if category.user_id is not None and category.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Category does not belong to you")
    return category


def create_category(db: Session, user: User, payload: CategoryCreate) -> Category:
    duplicate = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.type == payload.type,
            Category.status == CategoryStatus.ACTIVE.value,
            func.lower(Category.name) == payload.name.lower(),
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"An active {payload.type.lower()} category named '{payload.name}' already exists",
        )
    category = Category(
        user_id=user.id,
        name=payload.name,
        type=payload.type,
        icon=payload.icon,
        color=payload.color,
        is_system=False,
        status=CategoryStatus.ACTIVE.value,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session, user: User, category_id: uuid.UUID, payload: CategoryUpdate
) -> Category:
    category = get_owned_category(db, user, category_id)
    if category.is_system:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "System categories cannot be edited")
    if payload.name is not None:
        category.name = payload.name
    if payload.icon is not None:
        category.icon = payload.icon
    if payload.color is not None:
        category.color = payload.color
    db.commit()
    db.refresh(category)
    return category


def archive_category(db: Session, user: User, category_id: uuid.UUID) -> Category:
    category = get_owned_category(db, user, category_id)
    if category.is_system:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "System categories cannot be archived")
    category.status = CategoryStatus.ARCHIVED.value
    db.commit()
    db.refresh(category)
    return category
