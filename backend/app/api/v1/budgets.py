"""Budget endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.response import ok
from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetOut, BudgetUpdate
from app.services import budgets as budgets_service

router = APIRouter(tags=["budgets"])


@router.post("/budgets")
def create_budget(
    payload: BudgetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    budget = budgets_service.create_budget(db, user, payload)
    return ok(BudgetOut.model_validate(budget).model_dump(mode="json"))


@router.get("/budgets")
def list_budgets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    budgets = budgets_service.list_budgets(db, user)
    return ok([BudgetOut.model_validate(b).model_dump(mode="json") for b in budgets])


@router.get("/budgets/{budget_id}")
def get_budget(
    budget_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    budget = budgets_service.get_budget(db, user, budget_id)
    return ok(BudgetOut.model_validate(budget).model_dump(mode="json"))


@router.patch("/budgets/{budget_id}")
def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    budget = budgets_service.update_budget(db, user, budget_id, payload)
    return ok(BudgetOut.model_validate(budget).model_dump(mode="json"))


@router.delete("/budgets/{budget_id}")
def archive_budget(
    budget_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    budget = budgets_service.archive_budget(db, user, budget_id)
    return ok(BudgetOut.model_validate(budget).model_dump(mode="json"))


@router.get("/budgets/{budget_id}/performance")
def budget_performance(
    budget_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(budgets_service.performance(db, user, budget_id))
