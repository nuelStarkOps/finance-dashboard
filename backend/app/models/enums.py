"""Shared enumerations stored as strings in the database."""

from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class AccountType(StrEnum):
    CASH = "CASH"
    CURRENT = "CURRENT"
    SAVINGS = "SAVINGS"
    OTHER = "OTHER"


class AccountStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Theme(StrEnum):
    SYSTEM = "SYSTEM"
    LIGHT = "LIGHT"
    DARK = "DARK"
