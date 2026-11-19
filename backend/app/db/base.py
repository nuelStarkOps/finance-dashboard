"""Declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models.

    All user-owned tables are added in later phases and registered here so
    Alembic autogenerate can discover them.
    """
