from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from supabase import Client

from auth import get_current_user
from database import get_supabase
from models import (
    BudgetCategoryCreate,
    BudgetCategoryPublic,
    DashboardSummary,
    User,
)
from services import budget_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("/categories", response_model=BudgetCategoryPublic)
def create_category(
    body: BudgetCategoryCreate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return budget_service.create_category(supabase, user.id, body)


@router.get("/categories", response_model=List[BudgetCategoryPublic])
def list_categories(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return budget_service.get_categories(supabase, user.id)


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return budget_service.get_dashboard_summary(supabase, user.id)
