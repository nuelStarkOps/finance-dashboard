"""Savings goal endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.savings import ContributionCreate, ContributionOut, GoalCreate, GoalUpdate
from app.services import savings as savings_service

router = APIRouter(tags=["savings"])


@router.post("/savings/goals")
def create_goal(
    payload: GoalCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(savings_service.create_goal(db, user, payload))


@router.get("/savings/goals")
def list_goals(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(savings_service.list_goals(db, user))


@router.get("/savings/goals/{goal_id}")
def get_goal(
    goal_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(savings_service.get_goal(db, user, goal_id))


@router.patch("/savings/goals/{goal_id}")
def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(savings_service.update_goal(db, user, goal_id, payload))


@router.post("/savings/goals/{goal_id}/contributions")
def add_contribution(
    goal_id: uuid.UUID,
    payload: ContributionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    contribution = savings_service.add_contribution(db, user, goal_id, payload)
    return ok(ContributionOut.model_validate(contribution).model_dump(mode="json"))


@router.get("/savings/goals/{goal_id}/history")
def contribution_history(
    goal_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = savings_service.history(db, user, goal_id)
    return ok([ContributionOut.model_validate(c).model_dump(mode="json") for c in items])
