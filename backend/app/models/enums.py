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
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class TransactionType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"


class TransactionStatus(StrEnum):
    POSTED = "POSTED"
    VOIDED = "VOIDED"


class CategoryType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class CategoryStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class BudgetStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class GoalStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


class ContributionType(StrEnum):
    CONTRIBUTION = "CONTRIBUTION"
    WITHDRAWAL = "WITHDRAWAL"
    ADJUSTMENT = "ADJUSTMENT"


class BillFrequency(StrEnum):
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"
    CUSTOM = "CUSTOM"


class BillStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class OccurrenceStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    SKIPPED = "SKIPPED"
