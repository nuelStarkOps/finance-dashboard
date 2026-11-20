"""Savings goal service — goals, allocations and progress.

Allocations are virtual bookkeeping: they track progress toward a target but
never create account ledger movements (per spec §2.6).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import ContributionType, GoalStatus
from app.models.savings import GoalContribution, SavingsGoal
from app.models.user import User
from app.schemas.savings import ContributionCreate, GoalCreate, GoalOut, GoalUpdate

_ADDITIVE = (ContributionType.CONTRIBUTION.value, ContributionType.ADJUSTMENT.value)


def _owned(db: Session, user: User, goal_id: uuid.UUID) -> SavingsGoal:
    goal = db.get(SavingsGoal, goal_id)
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found")
    if goal.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Goal does not belong to you")
    return goal


def _allocated(db: Session, goal_id: uuid.UUID) -> int:
    additions = (
        db.query(func.coalesce(func.sum(GoalContribution.amount_minor), 0))
        .filter(
            GoalContribution.goal_id == goal_id,
            GoalContribution.contribution_type.in_(_ADDITIVE),
        )
        .scalar()
    )
    withdrawals = (
        db.query(func.coalesce(func.sum(GoalContribution.amount_minor), 0))
        .filter(
            GoalContribution.goal_id == goal_id,
            GoalContribution.contribution_type == ContributionType.WITHDRAWAL.value,
        )
        .scalar()
    )
    return int(additions or 0) - int(withdrawals or 0)


def _progress(goal: SavingsGoal, allocated: int) -> float:
    return round((allocated / goal.target_minor) * 100, 1)


def _goal_out(goal: SavingsGoal, db: Session) -> dict:
    allocated = _allocated(db, goal.id)
    data = GoalOut.model_validate(goal).model_dump(mode="json")
    data["allocated_minor"] = allocated
    data["progress_percent"] = _progress(goal, allocated)
    return data


def create_goal(db: Session, user: User, payload: GoalCreate) -> dict:
    goal = SavingsGoal(
        user_id=user.id,
        name=payload.name,
        currency_code=payload.currency_code,
        target_minor=payload.target_minor,
        target_date=payload.target_date,
        priority=payload.priority,
        status=GoalStatus.ACTIVE.value,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _goal_out(goal, db)


def list_goals(db: Session, user: User) -> list[dict]:
    goals = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.user_id == user.id)
        .order_by(SavingsGoal.created_at.desc())
        .all()
    )
    return [_goal_out(g, db) for g in goals]


def get_goal(db: Session, user: User, goal_id: uuid.UUID) -> dict:
    return _goal_out(_owned(db, user, goal_id), db)


def update_goal(db: Session, user: User, goal_id: uuid.UUID, payload: GoalUpdate) -> dict:
    goal = _owned(db, user, goal_id)
    if payload.name is not None:
        goal.name = payload.name
    if payload.target_minor is not None:
        goal.target_minor = payload.target_minor
    if payload.target_date is not None:
        goal.target_date = payload.target_date
    if payload.priority is not None:
        goal.priority = payload.priority
    if payload.status is not None:
        goal.status = payload.status
    db.commit()
    db.refresh(goal)
    return _goal_out(goal, db)


def add_contribution(
    db: Session, user: User, goal_id: uuid.UUID, payload: ContributionCreate
) -> dict:
    _owned(db, user, goal_id)
    contribution = GoalContribution(
        goal_id=goal_id,
        user_id=user.id,
        amount_minor=payload.amount_minor,
        contribution_type=payload.contribution_type,
        contribution_date=payload.contribution_date,
        notes=payload.notes,
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return contribution


def history(db: Session, user: User, goal_id: uuid.UUID) -> list:
    _owned(db, user, goal_id)
    return (
        db.query(GoalContribution)
        .filter(GoalContribution.goal_id == goal_id)
        .order_by(GoalContribution.contribution_date.desc(), GoalContribution.created_at.desc())
        .all()
    )
